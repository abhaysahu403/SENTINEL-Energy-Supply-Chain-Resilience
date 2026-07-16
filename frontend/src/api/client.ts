import axios from "axios";
import type {
  Corridor, ScenarioTemplate, Scenario, ProcurementRecommendation,
  ReserveStatus, AgentTrace, EventItem,
} from "../types";

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

const client = axios.create({ baseURL: API_BASE });

export function setAuthToken(token: string | null) {
  if (token) {
    client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common["Authorization"];
  }
}

export const api = {
  // --- risk -------------------------------------------------------------
  getCorridors: () => client.get<Corridor[]>("/api/risk/corridors").then(r => r.data),
  getCorridorHistory: (id: string) =>
    client.get(`/api/risk/corridors/${id}/history`).then(r => r.data),

  // --- scenarios ----------------------------------------------------------
  getScenarioTemplates: () => client.get<ScenarioTemplate[]>("/api/scenarios").then(r => r.data),
  runScenario: (templateId: string, overrides: { volume_loss_pct?: number; duration_days?: number }) =>
    client.post<Scenario>(`/api/scenarios/${templateId}/run`, overrides).then(r => r.data),
  getScenarioHistory: () => client.get<Scenario[]>("/api/scenarios/history").then(r => r.data),

  // --- procurement ----------------------------------------------------------
  getProcurementRecommendations: (scenarioId?: string) =>
    client.get<ProcurementRecommendation[]>("/api/procurement/recommendations", {
      params: scenarioId ? { scenario_id: scenarioId } : {},
    }).then(r => r.data),
  generateProcurement: (scenarioId: string) =>
    client.post<ProcurementRecommendation>(`/api/procurement/generate/${scenarioId}`).then(r => r.data),
  executeProcurement: (recommendationId: string) =>
    client.post(`/api/procurement/${recommendationId}/execute`).then(r => r.data),

  // --- reserves ----------------------------------------------------------
  getReserveStatus: () => client.get<ReserveStatus>("/api/reserves/status").then(r => r.data),
  simulateReserve: (scenarioId: string) =>
    client.post<ReserveStatus>("/api/reserves/simulate", { scenario_id: scenarioId }).then(r => r.data),
  getReserveHistory: () => client.get("/api/reserves/history").then(r => r.data),

  // --- trace / metrics / events ----------------------------------------------
  getTrace: (traceId: string) => client.get<AgentTrace>(`/api/trace/${traceId}`).then(r => r.data),
  listTraces: () => client.get<AgentTrace[]>("/api/trace").then(r => r.data),
  getResponseTimeMetrics: () => client.get("/api/metrics/response-time").then(r => r.data),
  getRecentEvents: () => client.get<EventItem[]>("/api/events/recent").then(r => r.data),
  injectEvent: (payload: {
    headline: string; raw_text: string; event_type: string;
    affected_corridor: string; affected_suppliers: string[]; severity: number;
  }) => client.post("/api/events/inject", payload).then(r => r.data),

  // --- auth ----------------------------------------------------------
  register: (payload: { email: string; password: string; full_name: string; role: string; organization?: string }) =>
    client.post("/api/auth/register", payload).then(r => r.data),
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return client.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }).then(r => r.data);
  },
  me: () => client.get("/api/auth/me").then(r => r.data),
};

export default client;
