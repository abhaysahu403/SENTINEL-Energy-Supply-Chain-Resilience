from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
import datetime as dt

from app.db.database import Base


def utcnow():
    return dt.datetime.utcnow()


class Corridor(Base):
    __tablename__ = "corridors"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    lon = Column(Float)
    lat = Column(Float)
    baseline_daily_volume_mbd = Column(Float)
    india_dependency_pct = Column(Float)
    note = Column(String)
    current_risk_score = Column(Float, default=10.0)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True)
    country = Column(String, nullable=False)
    crude_grade = Column(String)
    api_gravity = Column(Float)
    sulfur_pct = Column(Float)
    avg_spot_premium_usd_bbl = Column(Float)
    typical_transit_days_to_india = Column(Integer)
    primary_corridor = Column(String, ForeignKey("corridors.id"))
    current_daily_supply_to_india_mbd = Column(Float)
    sanctions_status = Column(String)
    notes = Column(String)


class Refinery(Base):
    __tablename__ = "refineries"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    operator = Column(String)
    lon = Column(Float)
    lat = Column(Float)
    capacity_mbd = Column(Float)
    grade_compatibility = Column(JSON)  # list[str]
    current_crude_mix = Column(JSON)    # dict[supplier_id -> fraction]


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    corridor_id = Column(String, ForeignKey("corridors.id"))
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)
    score = Column(Float, nullable=False)
    contributing_signals = Column(JSON)  # list of event ids + weights
    timestamp = Column(DateTime, default=utcnow)


class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    source = Column(String)
    headline = Column(String)
    raw_text = Column(String)
    event_type = Column(String)
    affected_corridor = Column(String, ForeignKey("corridors.id"), nullable=True)
    affected_suppliers = Column(JSON)  # list[str]
    severity = Column(Float)
    timestamp = Column(DateTime, default=utcnow)
    processed = Column(Integer, default=0)  # 0/1 boolean flag


class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(String, primary_key=True, default=lambda: None)
    template_id = Column(String)  # which of the 3 fixed templates
    name = Column(String)
    parameters = Column(JSON)
    results = Column(JSON)
    triggered_by_event_id = Column(String, ForeignKey("events.id"), nullable=True)
    run_timestamp = Column(DateTime, default=utcnow)


class ProcurementRecommendation(Base):
    __tablename__ = "procurement_recommendations"
    id = Column(String, primary_key=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
    ranked_options = Column(JSON)
    generated_at = Column(DateTime, default=utcnow)
    trace_id = Column(String)


class SPRStatus(Base):
    __tablename__ = "spr_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utcnow)
    days_of_cover = Column(Float)
    recommended_drawdown_mbd = Column(Float)
    schedule = Column(JSON)
    trace_id = Column(String)


class AgentTrace(Base):
    """
    One row per orchestration run. Stores which agents fired, in what order,
    on what inputs, and how long each step took -- this powers the
    Explainability / Agent Trace view on the frontend and the
    /metrics/response-time endpoint.
    """
    __tablename__ = "agent_traces"
    trace_id = Column(String, primary_key=True)
    triggered_by_event_id = Column(String, nullable=True)
    steps = Column(JSON)  # list of {agent, started_at, finished_at, summary}
    started_at = Column(DateTime, default=utcnow)
    finished_at = Column(DateTime, nullable=True)
    total_latency_ms = Column(Float, nullable=True)
