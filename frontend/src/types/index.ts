export interface Corridor {
  id: string;
  name: string;
  type: string;
  lon: number;
  lat: number;
  baseline_daily_volume_mbd: number;
  india_dependency_pct: number;
  current_risk_score: number;
  note: string;
}

export interface ContributingSignal {
  signal: string;
  raw_value: number | Record<string, unknown>;
  weight?: number;
  contribution?: number;
}

export interface RiskUpdatePayload {
  corridor_id: string;
  score: number;
  contributing_signals: ContributingSignal[];
  trace_id: string;
}

export interface ScenarioTemplate {
  template_id: string;
  label: string;
  affected_corridor: string;
  default_volume_loss_pct: number;
  default_duration_days: number;
  reroute_penalty_days?: number;
}

export interface RefineryImpact {
  refinery_id: string;
  name: string;
  exposure_fraction: number;
  run_rate_delta_pct: number;
}

export interface ScenarioResults {
  corridor_id: string;
  volume_loss_pct: number;
  duration_days: number;
  volume_lost_mbd: number;
  total_supply_at_risk_mbd: number;
  refinery_impacts: RefineryImpact[];
  implied_crude_price_shock_pct: number;
  fuel_price_delta_pct: number;
  retail_pass_through_days: number;
  power_sector: { gas_shortfall_proxy_pct: number; diesel_substitution_delta_pp: number };
  gdp_impact: { implied_brent_usd_shock: number; gdp_growth_delta_pp: number };
  assumptions_used: Record<string, number>;
}

export interface Scenario {
  id: string;
  template_id: string;
  name: string;
  parameters: Record<string, number>;
  results: ScenarioResults;
  run_timestamp?: string;
}

export interface ProcurementOption {
  supplier_id: string;
  country: string;
  crude_grade: string;
  cost_usd_bbl: number;
  delay_days: number;
  route_risk: number;
  max_available_mbd: number;
  grade_compatible: boolean;
  primary_corridor: string;
  sanctions_status: string;
  recommended_allocation_mbd: number;
  weighted_score: number;
  solver_status: string;
  total_demand_coverage_pct: number;
}

export interface ProcurementRecommendation {
  id: string;
  scenario_id: string;
  ranked_options: ProcurementOption[];
  generated_at: string;
  trace_id?: string;
}

export interface ReserveStatus {
  days_of_cover: number;
  recommended_drawdown_mbd: number;
  schedule: {
    solver_status: string;
    recommended_avg_daily_drawdown_mb: number;
    total_drawdown_mb: number;
    total_forecast_gap_mb: number;
    gap_coverage_pct: number;
    floor_reserve_mb: number;
    available_above_floor_mb: number;
    schedule: { day: number; drawdown_mb: number }[];
    assumptions: Record<string, number>;
  };
  timestamp?: string;
}

export interface AgentTraceStep {
  agent: string;
  latency_ms: number;
  timestamp: string;
  summary: Record<string, unknown>;
}

export interface AgentTrace {
  trace_id: string;
  triggered_by_event_id: string | null;
  steps: AgentTraceStep[];
  started_at: string;
  finished_at: string | null;
  total_latency_ms: number | null;
}

export interface EventItem {
  id: string;
  source: string;
  headline: string;
  event_type: string;
  affected_corridor: string;
  severity: number;
  timestamp: string;
}

export interface AlertPayload {
  level: "info" | "critical";
  message: string;
  trace_id: string;
}
