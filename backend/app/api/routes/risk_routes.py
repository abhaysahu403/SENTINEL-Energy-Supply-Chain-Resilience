from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Corridor, RiskScore

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/corridors")
def list_corridor_risk(db: Session = Depends(get_db)):
    corridors = db.query(Corridor).all()
    return [
        {
            "id": c.id, "name": c.name, "type": c.type,
            "lon": c.lon, "lat": c.lat,
            "baseline_daily_volume_mbd": c.baseline_daily_volume_mbd,
            "india_dependency_pct": c.india_dependency_pct,
            "current_risk_score": c.current_risk_score,
            "note": c.note,
        }
        for c in corridors
    ]


@router.get("/corridors/{corridor_id}/history")
def corridor_risk_history(corridor_id: str, limit: int = 50, db: Session = Depends(get_db)):
    scores = (
        db.query(RiskScore)
        .filter(RiskScore.corridor_id == corridor_id)
        .order_by(RiskScore.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "score": s.score, "timestamp": s.timestamp.isoformat(),
            "contributing_signals": s.contributing_signals,
        }
        for s in reversed(scores)
    ]
