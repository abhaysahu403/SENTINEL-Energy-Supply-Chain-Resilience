"""
M4 — Strategic Reserve Optimisation Agent.
Consumes the scenario's forecast supply gap and current SPR status, and
produces an optimal drawdown schedule via LP (app/ml/optimization.py).
"""
import json
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.db.models import Scenario, SPRStatus
from app.ml.optimization import optimize_spr_drawdown


def _load_spr_baseline():
    with open(DATA_DIR / "baseline.json") as f:
        return json.load(f)["spr"]


def recommend_drawdown(db: Session, scenario: Scenario, trace_id: str | None = None) -> SPRStatus:
    spr = _load_spr_baseline()
    results = scenario.results

    forecast_daily_gap_mbd = results["volume_lost_mbd"]
    duration_days = results["duration_days"]

    latest = db.query(SPRStatus).order_by(SPRStatus.timestamp.desc()).first()
    current_days_of_cover = latest.days_of_cover if latest else spr["days_of_cover"]

    optimization_result = optimize_spr_drawdown(
        current_days_of_cover=current_days_of_cover,
        total_capacity_mb=spr["total_capacity_mb"],
        forecast_daily_gap_mbd=forecast_daily_gap_mbd,
        disruption_duration_days=duration_days,
        national_daily_consumption_mb=spr["national_daily_consumption_mb"],
    )

    record = SPRStatus(
        days_of_cover=current_days_of_cover,
        recommended_drawdown_mbd=optimization_result["recommended_avg_daily_drawdown_mb"],
        schedule=optimization_result,
        trace_id=trace_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
