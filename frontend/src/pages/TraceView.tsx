import { useEffect, useState } from "react";
import { Panel, Button } from "../components/ui";
import { api } from "../api/client";
import type { AgentTrace } from "../types";

const AGENT_LABELS: Record<string, string> = {
  M1_risk_agent: "M1 · Geopolitical Risk Intelligence Agent",
  M2_scenario_agent: "M2 · Disruption Scenario Modeller",
  M3_procurement_agent: "M3 · Adaptive Procurement Orchestrator",
  M4_reserve_agent: "M4 · Strategic Reserve Optimisation Agent",
};

export function TraceView() {
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [selected, setSelected] = useState<AgentTrace | null>(null);
  const [metrics, setMetrics] = useState<{ avg_signal_to_recommendation_ms: number | null; p95_signal_to_recommendation_ms: number | null; n_traces: number } | null>(null);

  function refresh() {
    api.listTraces().then(setTraces);
    api.getResponseTimeMetrics().then(setMetrics);
  }

  useEffect(() => { refresh(); }, []);

  async function openTrace(traceId: string) {
    const full = await api.getTrace(traceId);
    setSelected(full);
  }

  return (
    <div className="p-6 max-w-[1400px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-lg tracking-[0.08em] mb-0.5">AGENT TRACE</h1>
          <p className="text-sm text-[var(--color-ink-muted)]">
            Full explainability: every step each agent took to produce a recommendation.
          </p>
        </div>
        <Button variant="ghost" onClick={refresh}>Refresh</Button>
      </div>

      {metrics && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          <Panel>
            <div className="font-display text-[10px] tracking-[0.14em] text-[var(--color-ink-faint)] uppercase mb-1">Avg Signal-to-Recommendation</div>
            <div className="font-display text-2xl text-[var(--color-phosphor)]">
              {metrics.avg_signal_to_recommendation_ms ? `${Math.round(metrics.avg_signal_to_recommendation_ms)}ms` : "—"}
            </div>
          </Panel>
          <Panel>
            <div className="font-display text-[10px] tracking-[0.14em] text-[var(--color-ink-faint)] uppercase mb-1">P95 Latency</div>
            <div className="font-display text-2xl">
              {metrics.p95_signal_to_recommendation_ms ? `${Math.round(metrics.p95_signal_to_recommendation_ms)}ms` : "—"}
            </div>
          </Panel>
          <Panel>
            <div className="font-display text-[10px] tracking-[0.14em] text-[var(--color-ink-faint)] uppercase mb-1">Total Traces Recorded</div>
            <div className="font-display text-2xl">{metrics.n_traces}</div>
          </Panel>
        </div>
      )}

      <div className="grid grid-cols-3 gap-5">
        <Panel eyebrow="Recent" title="Orchestration Runs">
          <div className="flex flex-col gap-1.5 max-h-[500px] overflow-y-auto">
            {traces.map((t) => (
              <button
                key={t.trace_id}
                onClick={() => openTrace(t.trace_id)}
                className={`text-left px-3 py-2 rounded-sm border text-xs font-display transition-colors ${
                  selected?.trace_id === t.trace_id
                    ? "border-[var(--color-phosphor)] text-[var(--color-phosphor)]"
                    : "border-[var(--color-hairline)] text-[var(--color-ink-muted)] hover:text-[var(--color-ink-bright)]"
                }`}
              >
                <div>{t.trace_id}</div>
                <div className="text-[var(--color-ink-faint)]">{t.total_latency_ms ?? "…"}ms</div>
              </button>
            ))}
            {traces.length === 0 && (
              <div className="text-sm text-[var(--color-ink-faint)] py-4 text-center">No traces yet.</div>
            )}
          </div>
        </Panel>

        <Panel eyebrow="Detail" title="Step-by-Step Chain" className="col-span-2">
          {!selected && (
            <div className="text-sm text-[var(--color-ink-faint)] py-10 text-center font-display">
              Select a trace to inspect its agent chain.
            </div>
          )}
          {selected && (
            <div className="flex flex-col gap-3">
              {selected.steps.map((step, i) => (
                <div key={i} className="relative pl-6 pb-3 border-l border-[var(--color-hairline)] last:border-transparent">
                  <div className="absolute left-[-5px] top-0 w-2.5 h-2.5 rounded-full bg-[var(--color-phosphor)]" />
                  <div className="text-sm font-medium">{AGENT_LABELS[step.agent] ?? step.agent}</div>
                  <div className="font-display text-[11px] text-[var(--color-ink-faint)] mt-0.5">
                    {step.latency_ms}ms · {new Date(step.timestamp).toLocaleTimeString()}
                  </div>
                  <pre className="font-display text-[11px] text-[var(--color-ink-muted)] mt-1.5 bg-[var(--color-hull-raised)] rounded-sm p-2 overflow-x-auto">
                    {JSON.stringify(step.summary, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
