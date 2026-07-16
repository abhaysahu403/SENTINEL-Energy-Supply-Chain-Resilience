import json
import logging
import datetime as dt
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.db.models import Corridor, Supplier, Refinery, Event, SPRStatus
from app.graph import knowledge_graph as kg

logger = logging.getLogger("sentinel.seed")


def _load_json(filename: str):
    with open(DATA_DIR / filename, "r") as f:
        return json.load(f)


def seed_all(db: Session):
    if db.query(Corridor).count() > 0:
        logger.info("Database already seeded; skipping.")
        _rebuild_graph(db)
        return

    corridors = _load_json("corridors.json")
    for c in corridors:
        db.add(Corridor(
            id=c["id"], name=c["name"], type=c["type"],
            lon=c["coordinates"][0], lat=c["coordinates"][1],
            baseline_daily_volume_mbd=c["baseline_daily_volume_mbd"],
            india_dependency_pct=c["india_dependency_pct"],
            note=c["note"], current_risk_score=10.0,
        ))

    suppliers = _load_json("suppliers.json")
    for s in suppliers:
        db.add(Supplier(
            id=s["id"], country=s["country"], crude_grade=s["crude_grade"],
            api_gravity=s["api_gravity"], sulfur_pct=s["sulfur_pct"],
            avg_spot_premium_usd_bbl=s["avg_spot_premium_usd_bbl"],
            typical_transit_days_to_india=s["typical_transit_days_to_india"],
            primary_corridor=s["primary_corridor"],
            current_daily_supply_to_india_mbd=s["current_daily_supply_to_india_mbd"],
            sanctions_status=s["sanctions_status"], notes=s["notes"],
        ))

    refineries = _load_json("refineries.json")
    for r in refineries:
        db.add(Refinery(
            id=r["id"], name=r["name"], operator=r["operator"],
            lon=r["location"][0], lat=r["location"][1],
            capacity_mbd=r["capacity_mbd"],
            grade_compatibility=r["grade_compatibility"],
            current_crude_mix=r["current_crude_mix"],
        ))

    events = _load_json("events_sample.json")
    for e in events:
        db.add(Event(
            id=e["id"], source=e["source"], headline=e["headline"],
            raw_text=e["raw_text"], event_type=e["event_type"],
            affected_corridor=e["affected_corridor"],
            affected_suppliers=e["affected_suppliers"],
            severity=e["severity"],
            timestamp=dt.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None),
            processed=1,
        ))

    baseline = _load_json("baseline.json")
    spr = baseline["spr"]
    db.add(SPRStatus(
        days_of_cover=spr["days_of_cover"],
        recommended_drawdown_mbd=0.0,
        schedule={"note": "baseline seed, no active drawdown"},
        trace_id="seed",
    ))

    db.commit()
    logger.info("Database seeded: %d corridors, %d suppliers, %d refineries, %d events",
                len(corridors), len(suppliers), len(refineries), len(events))
    _rebuild_graph(db)


def _rebuild_graph(db: Session):
    """(Re)build the knowledge graph nodes/edges from current DB state."""
    for c in db.query(Corridor).all():
        kg.upsert_node(c.id, "Corridor", {
            "name": c.name, "lon": c.lon, "lat": c.lat,
            "current_risk_score": c.current_risk_score,
        })
    for s in db.query(Supplier).all():
        kg.upsert_node(s.id, "Supplier", {
            "country": s.country, "crude_grade": s.crude_grade,
            "sanctions_status": s.sanctions_status,
        })
        if s.primary_corridor:
            kg.upsert_edge(s.id, s.primary_corridor, "SHIPS_VIA")
    for r in db.query(Refinery).all():
        kg.upsert_node(r.id, "Refinery", {
            "name": r.name, "capacity_mbd": r.capacity_mbd,
            "grade_compatibility": r.grade_compatibility,
        })
        for supplier_id in (r.current_crude_mix or {}):
            kg.upsert_edge(supplier_id, r.id, "SUPPLIES")
    logger.info("Knowledge graph rebuilt in %s mode.", kg.graph_mode())
