"""
ASSUMPTIONS LEDGER
===================
Every non-trivial coefficient used by the agents lives here, with a source
note. This module is imported by the Risk, Scenario, Procurement, and
Reserve agents rather than each hardcoding its own numbers -- so the whole
system's assumptions can be audited, challenged, and swapped for calibrated
values as real historical-event training data becomes available.

Where the codebase currently uses a hand-set heuristic weight, this file
documents WHY that weight was chosen and what it should be replaced with
once labeled historical outcome data exists.
"""

# ---------------------------------------------------------------------------
# M1: Geopolitical Risk Intelligence Agent — scoring weights
# ---------------------------------------------------------------------------
RISK_WEIGHTS = {
    # Direct severity of the extracted event (0-100, from NLP severity classifier)
    "event_severity": 0.40,
    # Rolling 90-day volatility of that corridor's historical risk score
    "historical_corridor_volatility": 0.20,
    # Change in sanctions-list entries relevant to the corridor/supplier in the last 30 days
    "sanctions_delta": 0.15,
    # Same-day commodity price shock (abs % change in Brent) as a market-implied risk signal
    "price_shock_signal": 0.15,
    # AIS traffic anomaly (|actual - baseline| / baseline) through the corridor
    "traffic_anomaly": 0.10,
}
assert abs(sum(RISK_WEIGHTS.values()) - 1.0) < 1e-6, "RISK_WEIGHTS must sum to 1.0"

RISK_SCORE_DECAY_HALF_LIFE_HOURS = 72
# Rationale: without new corroborating signals, a single event's contribution
# to the live score decays by half every 72 hours. Chosen as a starting
# heuristic (geopolitical news cycles typically resolve or escalate within
# 3-5 days); should be recalibrated against historical event-to-resolution
# timelines once available.

# ---------------------------------------------------------------------------
# M2: Disruption Scenario Modeller — cascading impact coefficients
# ---------------------------------------------------------------------------
FUEL_PRICE_ELASTICITY_TO_CRUDE = 0.35
# A 1% rise in landed crude cost passes through as ~0.35% rise in domestic
# retail fuel price over avg_retail_pass_through_days (see baseline.json).
# Order-of-magnitude consistent with PPAC pass-through studies; treat as
# a tunable parameter exposed in the UI, not a fixed truth.

RETAIL_PASS_THROUGH_DAYS = 12

POWER_SECTOR_DIESEL_SUBSTITUTION_PCT_PER_10PCT_GAS_SHORTFALL = 4.0
# For every 10% shortfall in gas-based power generation input (a proxy for
# broader energy-supply stress), diesel-based backup generation share rises
# by an estimated 4 percentage points. Placeholder heuristic pending
# grid-operator data integration (POSOCO/Grid-India public reports).

GDP_ELASTICITY_TO_10USD_OIL_SHOCK = -0.2
# A sustained +$10/bbl crude shock is associated with roughly -0.2 to -0.3
# percentage points of GDP growth drag for net oil importers of India's
# import-dependency profile (order-of-magnitude consistent with IMF/RBI
# published sensitivity ranges). Exposed as adjustable in the Scenario
# Simulator UI so a user can substitute their own estimate.

SCENARIO_TEMPLATES = {
    "hormuz_partial_closure": {
        "label": "Strait of Hormuz — Partial Closure",
        "affected_corridor": "hormuz",
        "default_volume_loss_pct": 50,
        "default_duration_days": 14,
    },
    "opec_emergency_cut": {
        "label": "OPEC+ Emergency Production Cut",
        "affected_corridor": "hormuz",
        "default_volume_loss_pct": 15,
        "default_duration_days": 60,
    },
    "red_sea_suspension": {
        "label": "Red Sea Shipping Lane Suspension",
        "affected_corridor": "bab_el_mandeb",
        "default_volume_loss_pct": 80,
        "default_duration_days": 30,
        "reroute_penalty_days": 12,  # extra transit time via Cape of Good Hope
    },
}

# ---------------------------------------------------------------------------
# M3: Adaptive Procurement Orchestrator — ranking weights (MILP objective)
# ---------------------------------------------------------------------------
PROCUREMENT_OBJECTIVE_WEIGHTS = {
    "cost_usd_bbl": 0.45,
    "delay_days": 0.30,
    "route_risk": 0.25,
}
assert abs(sum(PROCUREMENT_OBJECTIVE_WEIGHTS.values()) - 1.0) < 1e-6

TANKER_AVAILABILITY_DISCOUNT_PER_MBD_OVER_BASELINE = 0.08
# Assumed spot freight-rate premium (fractional increase) incurred per
# additional 0.1 mbd of sudden demand surge on a given route, reflecting
# tanker scarcity. Heuristic pending a real freight-index integration
# (Baltic Dirty Tanker Index).

# ---------------------------------------------------------------------------
# M4: Strategic Reserve Optimisation Agent
# ---------------------------------------------------------------------------
SPR_FLOOR_RESERVE_PCT = 20.0
# Never recommend drawing the SPR below 20% of total capacity in the
# optimizer, preserving an emergency floor regardless of forecast gap size.

SPR_MAX_DAILY_DRAWDOWN_MBD = 0.9
# Physical/logistical ceiling on how fast strategic reserves can be
# released to refiners per day (cavern withdrawal + pipeline/transport
# capacity constraint), based on ISPRL facility design parameters.
