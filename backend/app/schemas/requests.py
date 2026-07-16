from pydantic import BaseModel


class ScenarioRunRequest(BaseModel):
    # template_id is already supplied via the URL path
    # (/api/scenarios/{template_id}/run); only overrides go in the body.
    volume_loss_pct: float | None = None
    duration_days: int | None = None


class ManualEventRequest(BaseModel):
    headline: str
    raw_text: str
    event_type: str = "manual_injection"
    affected_corridor: str
    affected_suppliers: list[str] = []
    severity: float = 70.0
    source: str = "manual"


class ReserveOverrideRequest(BaseModel):
    scenario_id: str
