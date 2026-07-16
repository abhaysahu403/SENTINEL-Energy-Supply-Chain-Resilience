import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scenario, ProcurementRecommendation
from app.agents import procurement_agent

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


@router.get("/recommendations")
def get_recommendations(scenario_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(ProcurementRecommendation)
    if scenario_id:
        q = q.filter(ProcurementRecommendation.scenario_id == scenario_id)
    recs = q.order_by(ProcurementRecommendation.generated_at.desc()).limit(20).all()
    return [
        {"id": r.id, "scenario_id": r.scenario_id, "ranked_options": r.ranked_options,
         "generated_at": r.generated_at.isoformat(), "trace_id": r.trace_id}
        for r in recs
    ]


@router.post("/generate/{scenario_id}")
def generate_for_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    rec = procurement_agent.generate_recommendations(db, scenario)
    return {"id": rec.id, "scenario_id": rec.scenario_id, "ranked_options": rec.ranked_options}


@router.post("/{recommendation_id}/execute")
def execute_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    """
    Mock-executes a procurement recommendation: generates a procurement
    order summary. In a production deployment this would call out to a
    refiner's actual procurement/ERP system (e.g. SAP Ariba integration);
    here it returns a structured order confirmation for the demo.
    """
    rec = db.query(ProcurementRecommendation).filter(ProcurementRecommendation.id == recommendation_id).first()
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    top_option = rec.ranked_options[0] if rec.ranked_options else None
    if not top_option:
        raise HTTPException(status_code=400, detail="No ranked options on this recommendation")
    order = {
        "order_id": f"PO-{recommendation_id.upper()}",
        "supplier_id": top_option["supplier_id"],
        "country": top_option["country"],
        "volume_mbd": top_option["recommended_allocation_mbd"],
        "cost_usd_bbl": top_option["cost_usd_bbl"],
        "eta_days": top_option["delay_days"],
        "status": "confirmed",
        "confirmed_at": dt.datetime.utcnow().isoformat(),
    }
    return order
