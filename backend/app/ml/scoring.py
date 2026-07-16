"""
Core scoring math for the Risk Agent (M1). Kept separate from the agent's
orchestration logic (app/agents/risk_agent.py) so it's independently
unit-testable.
"""
import math
import datetime as dt

from app.agents.assumptions import RISK_WEIGHTS, RISK_SCORE_DECAY_HALF_LIFE_HOURS


def decay_factor(event_timestamp: dt.datetime, now: dt.datetime | None = None) -> float:
    """Exponential decay: contribution halves every RISK_SCORE_DECAY_HALF_LIFE_HOURS."""
    now = now or dt.datetime.utcnow()
    hours_elapsed = max(0.0, (now - event_timestamp).total_seconds() / 3600.0)
    return 0.5 ** (hours_elapsed / RISK_SCORE_DECAY_HALF_LIFE_HOURS)


def compute_corridor_risk_score(
    events: list[dict],
    historical_volatility: float,
    sanctions_delta: float,
    price_shock_pct: float,
    traffic_anomaly_pct: float,
    now: dt.datetime | None = None,
) -> tuple[float, list[dict]]:
    """
    Combine multiple weighted, time-decayed signals into a single 0-100
    disruption probability score for a corridor.

    Returns (score, contributing_signals) where contributing_signals is a
    list of {signal, raw_value, weight, contribution} dicts -- this is what
    gets stored in RiskScore.contributing_signals and surfaced in the
    Explainability view.
    """
    now = now or dt.datetime.utcnow()
    contributions = []

    # 1. Event severity component (time-decayed max of recent events)
    event_component = 0.0
    if events:
        decayed_severities = [
            e["severity"] * decay_factor(e["timestamp"], now) for e in events
        ]
        event_component = min(100.0, max(decayed_severities))
    w = RISK_WEIGHTS["event_severity"]
    contributions.append({"signal": "event_severity", "raw_value": round(event_component, 2),
                           "weight": w, "contribution": round(event_component * w, 2)})

    # 2. Historical volatility (already 0-100 scale)
    w = RISK_WEIGHTS["historical_corridor_volatility"]
    contributions.append({"signal": "historical_corridor_volatility", "raw_value": round(historical_volatility, 2),
                           "weight": w, "contribution": round(historical_volatility * w, 2)})

    # 3. Sanctions delta (normalize: assume 0-10 new designations -> 0-100)
    sanctions_norm = min(100.0, sanctions_delta * 10)
    w = RISK_WEIGHTS["sanctions_delta"]
    contributions.append({"signal": "sanctions_delta", "raw_value": round(sanctions_norm, 2),
                           "weight": w, "contribution": round(sanctions_norm * w, 2)})

    # 4. Price shock (normalize: assume 0-15% single-session move -> 0-100)
    price_norm = min(100.0, abs(price_shock_pct) / 15.0 * 100)
    w = RISK_WEIGHTS["price_shock_signal"]
    contributions.append({"signal": "price_shock_signal", "raw_value": round(price_norm, 2),
                           "weight": w, "contribution": round(price_norm * w, 2)})

    # 5. Traffic anomaly (normalize: assume 0-40% deviation -> 0-100)
    traffic_norm = min(100.0, abs(traffic_anomaly_pct) / 40.0 * 100)
    w = RISK_WEIGHTS["traffic_anomaly"]
    contributions.append({"signal": "traffic_anomaly", "raw_value": round(traffic_norm, 2),
                           "weight": w, "contribution": round(traffic_norm * w, 2)})

    score = round(sum(c["contribution"] for c in contributions), 2)
    score = max(0.0, min(100.0, score))
    return score, contributions
