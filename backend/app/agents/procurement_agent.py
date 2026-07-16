"""
M3 — Adaptive Procurement Orchestrator.
Given a scenario's supply gap, queries the knowledge graph for candidate
alternative suppliers/routes that avoid the affected corridor, then runs
the MILP ranking (app/ml/optimization.py) to produce executable
recommendations.
"""
import uuid
from sqlalchemy.orm import Session

from app.db.models import Supplier, Refinery, Scenario, ProcurementRecommendation
from app.graph import knowledge_graph as kg
from app.ml.optimization import rank_procurement_options
from app.agents.assumptions import TANKER_AVAILABILITY_DISCOUNT_PER_MBD_OVER_BASELINE


def generate_recommendations(db: Session, scenario: Scenario, trace_id: str | None = None) -> ProcurementRecommendation:
    results = scenario.results
    blocked_corridor = results["corridor_id"]
    volume_needed = results["volume_lost_mbd"]

    all_suppliers = db.query(Supplier).all()
    refineries = db.query(Refinery).all()
    all_grades = {r.id: set(r.grade_compatibility or []) for r in refineries}

    candidate_ids = [s.id for s in all_suppliers if s.sanctions_status != "us_sanctioned"]
    graph_routes = kg.find_alternative_routes(candidate_ids, blocked_corridor)
    routable_supplier_ids = {r["supplier_id"] for r in graph_routes} or set(candidate_ids)

    candidates = []
    for s in all_suppliers:
        if s.id not in routable_supplier_ids:
            continue
        if s.sanctions_status == "us_sanctioned":
            continue
        grade_compatible = any(s.crude_grade in grades for grades in all_grades.values())
        surge_available_mbd = max(0.0, 1.5 - s.current_daily_supply_to_india_mbd)  # simple headroom assumption
        freight_premium = 1 + (surge_available_mbd * TANKER_AVAILABILITY_DISCOUNT_PER_MBD_OVER_BASELINE)
        effective_cost = round(s.avg_spot_premium_usd_bbl * freight_premium, 2)
        route_risk = 15.0 if s.primary_corridor != blocked_corridor else 70.0

        candidates.append({
            "supplier_id": s.id,
            "country": s.country,
            "crude_grade": s.crude_grade,
            "cost_usd_bbl": effective_cost,
            "delay_days": s.typical_transit_days_to_india,
            "route_risk": route_risk,
            "max_available_mbd": round(surge_available_mbd, 3),
            "grade_compatible": grade_compatible,
            "primary_corridor": s.primary_corridor,
            "sanctions_status": s.sanctions_status,
        })

    ranked = rank_procurement_options(candidates, volume_needed_mbd=volume_needed)

    rec = ProcurementRecommendation(
        id=f"proc_{uuid.uuid4().hex[:10]}",
        scenario_id=scenario.id,
        ranked_options=ranked[:5],
        trace_id=trace_id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
