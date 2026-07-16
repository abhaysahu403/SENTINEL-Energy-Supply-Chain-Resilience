"""
M2 — Disruption Scenario Modeller.
Runs one of the three fixed scenario templates (see assumptions.py) with
either default or user-overridden parameters, and produces the cascading
impact chain: refinery run-rate -> fuel price -> power sector stress -> GDP.
Every output number is returned alongside the formula/coefficient that
produced it (the "show your work" panel on the frontend).
"""
import uuid
import json
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.db.models import Scenario, Refinery, Supplier, Corridor
from app.agents.assumptions import (
    SCENARIO_TEMPLATES,
    FUEL_PRICE_ELASTICITY_TO_CRUDE,
    RETAIL_PASS_THROUGH_DAYS,
    POWER_SECTOR_DIESEL_SUBSTITUTION_PCT_PER_10PCT_GAS_SHORTFALL,
    GDP_ELASTICITY_TO_10USD_OIL_SHOCK,
)


def _load_baseline():
    with open(DATA_DIR / "baseline.json") as f:
        return json.load(f)


def run_scenario(db: Session, template_id: str, overrides: dict | None = None,
                  triggered_by_event_id: str | None = None) -> Scenario:
    if template_id not in SCENARIO_TEMPLATES:
        raise ValueError(f"Unknown scenario template: {template_id}")

    template = SCENARIO_TEMPLATES[template_id]
    overrides = overrides or {}
    volume_loss_pct = overrides.get("volume_loss_pct", template["default_volume_loss_pct"])
    duration_days = overrides.get("duration_days", template["default_duration_days"])
    corridor_id = template["affected_corridor"]

    baseline = _load_baseline()
    corridor = db.query(Corridor).filter(Corridor.id == corridor_id).first()
    suppliers = db.query(Supplier).filter(Supplier.primary_corridor == corridor_id).all()
    refineries = db.query(Refinery).all()

    baseline_volume_mbd = corridor.baseline_daily_volume_mbd if corridor else 20.0

    # India's own volume at risk through this corridor is the sum of what
    # India's suppliers actually ship via it -- NOT the corridor's total
    # global transit volume (21 mbd through Hormuz is a global figure; only
    # ~2 mbd of that is India-bound). Using the global figure here would
    # wildly overstate India's own supply gap. This is the correct scale
    # for everything downstream (fuel price pass-through, SPR drawdown).
    total_supply_at_risk = sum(s.current_daily_supply_to_india_mbd for s in suppliers)
    volume_lost_mbd = round(total_supply_at_risk * (volume_loss_pct / 100.0), 3)

    # --- Refinery run-rate impact ---------------------------------------
    refinery_impacts = []
    for r in refineries:
        exposure = sum(
            frac for sid, frac in (r.current_crude_mix or {}).items()
            if sid in {s.id for s in suppliers}
        )
        run_rate_delta_pct = -round(exposure * volume_loss_pct, 2)
        refinery_impacts.append({
            "refinery_id": r.id,
            "name": r.name,
            "exposure_fraction": round(exposure, 3),
            "run_rate_delta_pct": run_rate_delta_pct,
        })

    # --- Domestic fuel price pass-through --------------------------------
    # Approximate crude cost shock % from volume loss via a simple
    # supply-shortage-to-price heuristic: price impact scales with the
    # fraction of national import volume affected, amplified for larger
    # single-corridor dependency (this corridor's india_dependency_pct).
    dependency_pct = corridor.india_dependency_pct if corridor else 30.0
    implied_crude_price_shock_pct = round((volume_loss_pct / 100.0) * (dependency_pct / 100.0) * 100, 2)
    fuel_price_delta_pct = round(implied_crude_price_shock_pct * FUEL_PRICE_ELASTICITY_TO_CRUDE, 2)

    # --- Power sector stress ----------------------------------------------
    gas_shortfall_proxy_pct = round(implied_crude_price_shock_pct * 0.6, 2)  # explicit simplifying proxy
    diesel_substitution_pp = round(
        (gas_shortfall_proxy_pct / 10.0) * POWER_SECTOR_DIESEL_SUBSTITUTION_PCT_PER_10PCT_GAS_SHORTFALL, 2
    )

    # --- GDP trajectory impact ---------------------------------------------
    brent_baseline_usd = 75.0
    implied_usd_shock = round(brent_baseline_usd * (implied_crude_price_shock_pct / 100.0), 2)
    gdp_growth_delta_pp = round((implied_usd_shock / 10.0) * GDP_ELASTICITY_TO_10USD_OIL_SHOCK, 3)

    results = {
        "corridor_id": corridor_id,
        "volume_loss_pct": volume_loss_pct,
        "duration_days": duration_days,
        "volume_lost_mbd": volume_lost_mbd,
        "total_supply_at_risk_mbd": round(total_supply_at_risk, 3),
        "refinery_impacts": refinery_impacts,
        "implied_crude_price_shock_pct": implied_crude_price_shock_pct,
        "fuel_price_delta_pct": fuel_price_delta_pct,
        "retail_pass_through_days": RETAIL_PASS_THROUGH_DAYS,
        "power_sector": {
            "gas_shortfall_proxy_pct": gas_shortfall_proxy_pct,
            "diesel_substitution_delta_pp": diesel_substitution_pp,
        },
        "gdp_impact": {
            "implied_brent_usd_shock": implied_usd_shock,
            "gdp_growth_delta_pp": gdp_growth_delta_pp,
        },
        "assumptions_used": {
            "fuel_price_elasticity_to_crude": FUEL_PRICE_ELASTICITY_TO_CRUDE,
            "power_sector_diesel_substitution_pct_per_10pct_gas_shortfall":
                POWER_SECTOR_DIESEL_SUBSTITUTION_PCT_PER_10PCT_GAS_SHORTFALL,
            "gdp_elasticity_to_10usd_oil_shock": GDP_ELASTICITY_TO_10USD_OIL_SHOCK,
        },
    }

    scenario = Scenario(
        id=f"scn_{uuid.uuid4().hex[:10]}",
        template_id=template_id,
        name=template["label"],
        parameters={"volume_loss_pct": volume_loss_pct, "duration_days": duration_days},
        results=results,
        triggered_by_event_id=triggered_by_event_id,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario
