from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SPRStatus, Scenario
from app.agents import reserve_agent
from app.schemas.requests import ReserveOverrideRequest

router = APIRouter(prefix="/api/reserves", tags=["reserves"])


@router.get("/status")
def current_status(db: Session = Depends(get_db)):
    latest = db.query(SPRStatus).order_by(SPRStatus.timestamp.desc()).first()
    if latest is None:
        raise HTTPException(status_code=404, detail="No SPR status recorded yet")
    return {
        "days_of_cover": latest.days_of_cover,
        "recommended_drawdown_mbd": latest.recommended_drawdown_mbd,
        "schedule": latest.schedule,
        "timestamp": latest.timestamp.isoformat(),
    }


@router.post("/simulate")
def simulate(payload: ReserveOverrideRequest, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == payload.scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    record = reserve_agent.recommend_drawdown(db, scenario)
    return {
        "days_of_cover": record.days_of_cover,
        "recommended_drawdown_mbd": record.recommended_drawdown_mbd,
        "schedule": record.schedule,
    }


@router.get("/history")
def history(limit: int = 20, db: Session = Depends(get_db)):
    records = db.query(SPRStatus).order_by(SPRStatus.timestamp.desc()).limit(limit).all()
    return [
        {"days_of_cover": r.days_of_cover, "recommended_drawdown_mbd": r.recommended_drawdown_mbd,
         "timestamp": r.timestamp.isoformat()}
        for r in reversed(records)
    ]
