"""
Orchestrator Agent — the multi-agent state machine described in the
architecture doc, Section 3.2 / 5.2.2.

Flow per incoming event:
  ingest -> M1 (risk score) -> [threshold check] -> M2 (scenario)
         -> M3 (procurement) -> M4 (reserves) -> broadcast + persist trace

Every step is timed and logged into AgentTrace so the frontend's
Explainability view and the /api/metrics/response-time endpoint have
real data to show, not placeholders.
"""
import time
import uuid
import logging
import datetime as dt
from sqlalchemy.orm import Session

from app.config import RISK_AUTO_TRIGGER_THRESHOLD
from app.db.database import SessionLocal
from app.db.models import Event, AgentTrace
from app.agents import risk_agent, scenario_agent, procurement_agent, reserve_agent
from app.agents.assumptions import SCENARIO_TEMPLATES
from app.websocket.manager import manager

logger = logging.getLogger("sentinel.orchestrator")

CORRIDOR_TO_TEMPLATE = {
    "hormuz": "hormuz_partial_closure",
    "bab_el_mandeb": "red_sea_suspension",
}


def _new_trace_id() -> str:
    return f"trc_{uuid.uuid4().hex[:12]}"


async def handle_incoming_event(event: dict):
    """
    Entry point invoked by the ingestion event bus consumer
    (app/ingestion/event_bus.py) for each new normalized event.
    Runs synchronous DB/CPU work in a fresh session; safe to call from an
    asyncio task since PuLP/DB calls here are fast (<1s) for hackathon scale.
    """
    db: Session = SessionLocal()
    trace_id = _new_trace_id()
    steps = []
    t_start = time.perf_counter()

    try:
        raw_ts = event.get("timestamp")
        if isinstance(raw_ts, str):
            parsed_ts = dt.datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
        elif isinstance(raw_ts, dt.datetime):
            parsed_ts = raw_ts
        else:
            parsed_ts = dt.datetime.utcnow()

        db_event = Event(
            id=event.get("id") or f"evt_{uuid.uuid4().hex[:10]}",
            source=event.get("source", "unknown"),
            headline=event.get("headline", ""),
            raw_text=event.get("raw_text", ""),
            event_type=event.get("event_type", "unclassified"),
            affected_corridor=event.get("affected_corridor"),
            affected_suppliers=event.get("affected_suppliers", []),
            severity=float(event.get("severity", 30.0)),
            timestamp=parsed_ts,
            processed=0,
        )
        db.merge(db_event)
        db.commit()

        corridor_id = db_event.affected_corridor
        if not corridor_id:
            logger.info("Event %s has no affected corridor; skipping agent chain.", db_event.id)
            return

        # --- M1: Risk scoring ------------------------------------------------
        # Derive proxy market/sanctions signals from the event itself: severe
        # geopolitical events are empirically correlated with same-day price
        # reaction and, for sanctions-type events, registry deltas. This is
        # an explicit modeling assumption (see assumptions.py) standing in
        # for a live price-feed/OFAC-diff join, and is documented as such.
        severity = float(event.get("severity", 30.0))
        price_shock_proxy_pct = round((severity / 100.0) * 9.0, 2)  # scale to ~0-9% single-session move
        sanctions_delta_proxy = 3.0 if event.get("event_type") == "sanctions_expansion" else 0.0

        t0 = time.perf_counter()
        risk_record = risk_agent.score_corridor(
            db, corridor_id,
            price_shock_pct=price_shock_proxy_pct,
            sanctions_delta=sanctions_delta_proxy,
        )
        steps.append(_step("M1_risk_agent", t0, {
            "corridor_id": corridor_id, "score": risk_record.score,
        }))
        await manager.broadcast("risk_update", {
            "corridor_id": corridor_id, "score": risk_record.score,
            "contributing_signals": risk_record.contributing_signals,
            "trace_id": trace_id,
        })

        db_event.processed = 1
        db.commit()

        if risk_record.score < RISK_AUTO_TRIGGER_THRESHOLD:
            logger.info("Risk score %.1f below trigger threshold %.1f; chain stops after M1.",
                        risk_record.score, RISK_AUTO_TRIGGER_THRESHOLD)
            await manager.broadcast("alert", {
                "level": "info", "message": f"New signal processed for {corridor_id}; risk score {risk_record.score}",
                "trace_id": trace_id,
            })
            return

        template_id = CORRIDOR_TO_TEMPLATE.get(corridor_id, "hormuz_partial_closure")

        # --- M2: Scenario modelling -------------------------------------------
        t0 = time.perf_counter()
        scenario = scenario_agent.run_scenario(db, template_id, triggered_by_event_id=db_event.id)
        steps.append(_step("M2_scenario_agent", t0, {
            "scenario_id": scenario.id, "template_id": template_id,
        }))
        await manager.broadcast("scenario_result", {"scenario": _scenario_to_dict(scenario), "trace_id": trace_id})

        # --- M3: Procurement ranking -------------------------------------------
        t0 = time.perf_counter()
        procurement = procurement_agent.generate_recommendations(db, scenario, trace_id=trace_id)
        steps.append(_step("M3_procurement_agent", t0, {
            "recommendation_id": procurement.id, "n_options": len(procurement.ranked_options),
        }))
        await manager.broadcast("procurement_recommendation", {
            "recommendation_id": procurement.id, "scenario_id": scenario.id,
            "ranked_options": procurement.ranked_options, "trace_id": trace_id,
        })

        # --- M4: Reserve drawdown -------------------------------------------
        t0 = time.perf_counter()
        spr_status = reserve_agent.recommend_drawdown(db, scenario, trace_id=trace_id)
        steps.append(_step("M4_reserve_agent", t0, {
            "spr_status_id": spr_status.id, "recommended_drawdown_mbd": spr_status.recommended_drawdown_mbd,
        }))
        await manager.broadcast("reserve_update", {
            "days_of_cover": spr_status.days_of_cover,
            "recommended_drawdown_mbd": spr_status.recommended_drawdown_mbd,
            "schedule": spr_status.schedule, "trace_id": trace_id,
        })

        await manager.broadcast("alert", {
            "level": "critical",
            "message": f"High-risk event on {corridor_id} (score {risk_record.score}) — "
                       f"full response chain generated in {round((time.perf_counter()-t_start)*1000)}ms",
            "trace_id": trace_id,
        })

    finally:
        total_ms = round((time.perf_counter() - t_start) * 1000, 1)
        trace = AgentTrace(
            trace_id=trace_id,
            triggered_by_event_id=event.get("id"),
            steps=steps,
            finished_at=dt.datetime.utcnow(),
            total_latency_ms=total_ms,
        )
        db.add(trace)
        db.commit()
        db.close()
        logger.info("Orchestration trace %s complete in %sms (%d steps)", trace_id, total_ms, len(steps))


def _step(agent_name: str, t0: float, summary: dict) -> dict:
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "agent": agent_name,
        "latency_ms": latency_ms,
        "timestamp": dt.datetime.utcnow().isoformat(),
        "summary": summary,
    }


def _scenario_to_dict(scenario) -> dict:
    return {
        "id": scenario.id,
        "template_id": scenario.template_id,
        "name": scenario.name,
        "parameters": scenario.parameters,
        "results": scenario.results,
    }
