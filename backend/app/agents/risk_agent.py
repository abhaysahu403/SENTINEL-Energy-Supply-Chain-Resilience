"""
M1 — Geopolitical Risk Intelligence Agent.
Ingests recent events for a corridor, pulls supporting signals (sanctions
delta, price shock, AIS traffic anomaly), and produces a live disruption
probability score, persisting it and pushing the update into the
knowledge graph so downstream agents (M3) see current risk immediately.
"""
import datetime as dt
from sqlalchemy.orm import Session

from app.db.models import Event, RiskScore, Corridor
from app.ml.scoring import compute_corridor_risk_score
from app.graph import knowledge_graph as kg
from app.ingestion.ais_client import fetch_simulated_ais


def _recent_events_for_corridor(db: Session, corridor_id: str, lookback_hours: int = 168) -> list[dict]:
    cutoff = dt.datetime.utcnow() - dt.timedelta(hours=lookback_hours)
    events = (
        db.query(Event)
        .filter(Event.affected_corridor == corridor_id)
        .filter(Event.timestamp >= cutoff)
        .all()
    )
    return [{"severity": e.severity, "timestamp": e.timestamp} for e in events]


def score_corridor(db: Session, corridor_id: str, price_shock_pct: float = 0.0,
                    sanctions_delta: float = 0.0) -> RiskScore:
    corridor = db.query(Corridor).filter(Corridor.id == corridor_id).first()
    if corridor is None:
        raise ValueError(f"Unknown corridor: {corridor_id}")

    events = _recent_events_for_corridor(db, corridor_id)

    # historical volatility proxy: stdev of the corridor's last 20 scores
    past_scores = (
        db.query(RiskScore)
        .filter(RiskScore.corridor_id == corridor_id)
        .order_by(RiskScore.timestamp.desc())
        .limit(20)
        .all()
    )
    if len(past_scores) >= 2:
        vals = [p.score for p in past_scores]
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        historical_volatility = min(100.0, variance ** 0.5)
    else:
        historical_volatility = 15.0  # low-information prior

    ais_snapshot = fetch_simulated_ais(corridor_id=corridor_id)

    score, contributions = compute_corridor_risk_score(
        events=events,
        historical_volatility=historical_volatility,
        sanctions_delta=sanctions_delta,
        price_shock_pct=price_shock_pct,
        traffic_anomaly_pct=ais_snapshot["traffic_anomaly_pct"],
    )

    record = RiskScore(
        corridor_id=corridor_id,
        supplier_id=None,
        score=score,
        contributing_signals=contributions + [{"signal": "ais_snapshot", "raw_value": ais_snapshot}],
    )
    db.add(record)
    corridor.current_risk_score = score
    db.commit()
    db.refresh(record)

    kg.set_corridor_risk(corridor_id, score)
    return record


def score_all_corridors(db: Session) -> list[RiskScore]:
    corridors = db.query(Corridor).all()
    return [score_corridor(db, c.id) for c in corridors]
