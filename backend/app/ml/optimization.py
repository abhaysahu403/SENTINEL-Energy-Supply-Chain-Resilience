"""
Real optimization models (not heuristic sorts) backing M3 and M4.
Uses PuLP (CBC solver, bundled — no external solver install required).
"""
import pulp

from app.agents.assumptions import (
    PROCUREMENT_OBJECTIVE_WEIGHTS,
    TANKER_AVAILABILITY_DISCOUNT_PER_MBD_OVER_BASELINE,
    SPR_FLOOR_RESERVE_PCT,
    SPR_MAX_DAILY_DRAWDOWN_MBD,
)


def rank_procurement_options(candidates: list[dict], volume_needed_mbd: float) -> list[dict]:
    """
    candidates: list of dicts with keys:
        supplier_id, cost_usd_bbl, delay_days, route_risk (0-100),
        max_available_mbd, grade_compatible (bool)
    volume_needed_mbd: total volume gap to fill

    Builds a small MILP: choose a fractional allocation x_i in [0, max_available_i]
    for each compatible candidate to cover volume_needed_mbd at minimum weighted
    cost (cost, delay, risk — weights from assumptions.py), then returns the
    candidates ranked by their normalized weighted score, annotated with the
    solver's recommended allocation fraction.
    """
    compatible = [c for c in candidates if c.get("grade_compatible", True)]
    if not compatible:
        return []

    prob = pulp.LpProblem("procurement_allocation", pulp.LpMinimize)
    x = {c["supplier_id"]: pulp.LpVariable(f"x_{c['supplier_id']}", lowBound=0,
                                            upBound=c["max_available_mbd"])
         for c in compatible}

    # Normalize each metric 0-1 across candidates so weights are comparable
    costs = [c["cost_usd_bbl"] for c in compatible]
    delays = [c["delay_days"] for c in compatible]
    risks = [c["route_risk"] for c in compatible]
    c_min, c_max = min(costs), max(costs) or 1
    d_min, d_max = min(delays), max(delays) or 1
    r_min, r_max = min(risks), max(risks) or 1

    def norm(v, lo, hi):
        return (v - lo) / (hi - lo) if hi > lo else 0.0

    w = PROCUREMENT_OBJECTIVE_WEIGHTS
    shortfall = pulp.LpVariable("shortfall", lowBound=0)
    SHORTFALL_PENALTY = 1000  # dominates the objective so the solver always tries to minimize unmet demand first

    prob += pulp.lpSum([
        x[c["supplier_id"]] * (
            w["cost_usd_bbl"] * norm(c["cost_usd_bbl"], c_min, c_max) +
            w["delay_days"] * norm(c["delay_days"], d_min, d_max) +
            w["route_risk"] * norm(c["route_risk"], r_min, r_max)
        )
        for c in compatible
    ]) + SHORTFALL_PENALTY * shortfall

    # Soft demand constraint: cover as much of volume_needed_mbd as possible;
    # `shortfall` absorbs whatever the combined surge capacity can't reach,
    # which is realistic -- a single chokepoint's full volume often cannot
    # be replaced instantly, and the system should say so explicitly rather
    # than fail. The Procurement Console surfaces `coverage_pct` for this.
    prob += pulp.lpSum(x.values()) + shortfall >= volume_needed_mbd, "meet_demand_soft"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    total_allocated = sum((x[c["supplier_id"]].value() or 0.0) for c in compatible)
    coverage_pct = round(min(100.0, (total_allocated / volume_needed_mbd) * 100), 1) if volume_needed_mbd > 0 else 100.0

    ranked = []
    for c in compatible:
        allocation = x[c["supplier_id"]].value() or 0.0
        weighted_score = (
            w["cost_usd_bbl"] * norm(c["cost_usd_bbl"], c_min, c_max) +
            w["delay_days"] * norm(c["delay_days"], d_min, d_max) +
            w["route_risk"] * norm(c["route_risk"], r_min, r_max)
        )
        ranked.append({
            **c,
            "recommended_allocation_mbd": round(allocation, 3),
            "weighted_score": round(weighted_score, 4),
            "solver_status": pulp.LpStatus[prob.status],
            "total_demand_coverage_pct": coverage_pct,
        })
    ranked.sort(key=lambda r: (r["weighted_score"], -r["recommended_allocation_mbd"]))
    return ranked


def optimize_spr_drawdown(
    current_days_of_cover: float,
    total_capacity_mb: float,
    forecast_daily_gap_mbd: float,
    disruption_duration_days: int,
    national_daily_consumption_mb: float,
) -> dict:
    """
    LP: choose a daily drawdown rate over the disruption window that closes
    the forecast supply gap while (a) never breaching the floor reserve and
    (b) never exceeding the physical max daily drawdown rate.
    """
    floor_mb = total_capacity_mb * (SPR_FLOOR_RESERVE_PCT / 100.0)
    current_mb = current_days_of_cover * national_daily_consumption_mb
    available_mb = max(0.0, current_mb - floor_mb)

    prob = pulp.LpProblem("spr_drawdown", pulp.LpMinimize)
    days = list(range(disruption_duration_days))
    draw = {d: pulp.LpVariable(f"draw_{d}", lowBound=0, upBound=SPR_MAX_DAILY_DRAWDOWN_MBD)
            for d in days}  # mb/day, consistent with total_capacity_mb / national_daily_consumption_mb

    shortfall = pulp.LpVariable("spr_shortfall", lowBound=0)
    SHORTFALL_PENALTY = 1000

    # Cover the forecast gap first (heavily penalized shortfall), then among
    # feasible schedules prefer conserving reserves. Mirrors the procurement
    # agent's soft-constraint pattern: a disruption can exceed what the SPR
    # alone can cover, and the system should say so via coverage_pct rather
    # than fail outright.
    prob += pulp.lpSum(draw.values()) + SHORTFALL_PENALTY * shortfall
    total_gap_mb = forecast_daily_gap_mbd * disruption_duration_days
    prob += pulp.lpSum(draw.values()) + shortfall >= total_gap_mb, "cover_gap_soft"
    prob += pulp.lpSum(draw.values()) <= available_mb, "floor_reserve_constraint"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    schedule = [{"day": d, "drawdown_mb": round((draw[d].value() or 0.0), 4)} for d in days]
    total_drawdown = sum(s["drawdown_mb"] for s in schedule)
    avg_daily = total_drawdown / disruption_duration_days if disruption_duration_days else 0.0
    coverage_pct = round(min(100.0, (total_drawdown / total_gap_mb) * 100), 1) if total_gap_mb > 0 else 100.0

    return {
        "solver_status": pulp.LpStatus[prob.status],
        "recommended_avg_daily_drawdown_mb": round(avg_daily, 4),
        "total_drawdown_mb": round(total_drawdown, 3),
        "total_forecast_gap_mb": round(total_gap_mb, 3),
        "gap_coverage_pct": coverage_pct,
        "floor_reserve_mb": round(floor_mb, 2),
        "available_above_floor_mb": round(available_mb, 2),
        "schedule": schedule,
        "assumptions": {
            "floor_reserve_pct": SPR_FLOOR_RESERVE_PCT,
            "max_daily_drawdown_mbd": SPR_MAX_DAILY_DRAWDOWN_MBD,
        },
    }
