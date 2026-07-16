import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import AgentTrace, Event
from app.schemas.requests import ManualEventRequest
from app.ingestion.event_bus import publish_event
from app.websocket.manager import manager

router = APIRouter(tags=["trace-metrics-events"])


@router.get("/api/trace/{trace_id}")
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    trace = db.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).first()
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "trace_id": trace.trace_id,
        "triggered_by_event_id": trace.triggered_by_event_id,
        "steps": trace.steps,
        "started_at": trace.started_at.isoformat(),
        "finished_at": trace.finished_at.isoformat() if trace.finished_at else None,
        "total_latency_ms": trace.total_latency_ms,
    }


@router.get("/api/trace")
def list_traces(limit: int = 20, db: Session = Depends(get_db)):
    traces = db.query(AgentTrace).order_by(AgentTrace.started_at.desc()).limit(limit).all()
    return [
        {"trace_id": t.trace_id, "total_latency_ms": t.total_latency_ms,
         "started_at": t.started_at.isoformat(), "n_steps": len(t.steps or [])}
        for t in traces
    ]


@router.get("/api/metrics/response-time")
def response_time_metrics(db: Session = Depends(get_db)):
    """
    Live signal-to-recommendation latency metric, computed from real
    AgentTrace rows -- not a hardcoded demo number.
    """
    avg_ms = db.query(func.avg(AgentTrace.total_latency_ms)).scalar()
    p95_candidates = [
        t.total_latency_ms for t in db.query(AgentTrace).filter(AgentTrace.total_latency_ms.isnot(None)).all()
    ]
    p95_candidates.sort()
    p95_ms = None
    if p95_candidates:
        idx = min(len(p95_candidates) - 1, int(0.95 * len(p95_candidates)))
        p95_ms = p95_candidates[idx]
    return {
        "avg_signal_to_recommendation_ms": round(avg_ms, 1) if avg_ms else None,
        "p95_signal_to_recommendation_ms": p95_ms,
        "n_traces": len(p95_candidates),
    }


@router.post("/api/events/inject")
async def inject_event(payload: ManualEventRequest):
    """
    Manually inject a new geopolitical event -- this is the button the live
    demo uses to trigger the full M1->M2->M3->M4 chain in real time.
    """
    import uuid
    import datetime as dt
    event = {
        "id": f"evt_manual_{uuid.uuid4().hex[:8]}",
        "source": payload.source,
        "headline": payload.headline,
        "raw_text": payload.raw_text,
        "event_type": payload.event_type,
        "affected_corridor": payload.affected_corridor,
        "affected_suppliers": payload.affected_suppliers,
        "severity": payload.severity,
        "timestamp": dt.datetime.utcnow().isoformat(),
    }
    await publish_event(event)
    return {"status": "queued", "event_id": event["id"]}


@router.get("/api/events/recent")
def recent_events(limit: int = 20, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
    return [
        {"id": e.id, "source": e.source, "headline": e.headline, "event_type": e.event_type,
         "affected_corridor": e.affected_corridor, "severity": e.severity,
         "timestamp": e.timestamp.isoformat()}
        for e in events
    ]


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Frontend doesn't need to send anything; this just keeps the
            # connection alive and detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
