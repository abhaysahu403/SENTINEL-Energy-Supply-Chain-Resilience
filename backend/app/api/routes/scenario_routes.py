from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scenario
from app.agents import scenario_agent
from app.agents.assumptions import SCENARIO_TEMPLATES
from app.schemas.requests import ScenarioRunRequest

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
def list_templates():
    return [{"template_id": k, **v} for k, v in SCENARIO_TEMPLATES.items()]


@router.post("/{template_id}/run")
def run_scenario(template_id: str, payload: ScenarioRunRequest, db: Session = Depends(get_db)):
    if template_id not in SCENARIO_TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown scenario template")
    overrides = {}
    if payload.volume_loss_pct is not None:
        overrides["volume_loss_pct"] = payload.volume_loss_pct
    if payload.duration_days is not None:
        overrides["duration_days"] = payload.duration_days
    scenario = scenario_agent.run_scenario(db, template_id, overrides=overrides)
    return {
        "id": scenario.id, "template_id": scenario.template_id, "name": scenario.name,
        "parameters": scenario.parameters, "results": scenario.results,
        "run_timestamp": scenario.run_timestamp.isoformat(),
    }


@router.get("/history")
def scenario_history(limit: int = 20, db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).order_by(Scenario.run_timestamp.desc()).limit(limit).all()
    return [
        {"id": s.id, "template_id": s.template_id, "name": s.name,
         "run_timestamp": s.run_timestamp.isoformat(), "results": s.results}
        for s in scenarios
    ]
