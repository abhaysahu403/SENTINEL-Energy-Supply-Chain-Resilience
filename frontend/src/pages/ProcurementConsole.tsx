import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Panel, Button } from "../components/ui";
import { api } from "../api/client";
import type { ProcurementRecommendation, ProcurementOption } from "../types";

export function ProcurementConsole() {
  const [params] = useSearchParams();
  const scenarioId = params.get("scenario_id") || undefined;
  const [recs, setRecs] = useState<ProcurementRecommendation[]>([]);
  const [executing, setExecuting] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.getProcurementRecommendations(scenarioId).then(setRecs);
  }, [scenarioId]);

  async function execute(recId: string) {
    setExecuting(recId);
    try {
      const order = await api.executeProcurement(recId);
      setConfirmation(order);
    } finally {
      setExecuting(null);
    }
  }

  const latest = recs[0];

  return (
    <div className="p-6 max-w-[1400px]">
      <h1 className="font-display text-lg tracking-[0.08em] mb-0.5">PROCUREMENT CONSOLE</h1>
      <p className="text-sm text-[var(--color-ink-muted)] mb-6">
        Ranked alternative crude sourcing options — MILP-optimized on cost, delay, and route risk.
      </p>

      {!latest && (
        <Panel className="text-sm text-[var(--color-ink-faint)] font-display py-10 text-center">
          No recommendations yet — run a scenario in the Simulator first.
        </Panel>
      )}

      {latest && (
        <>
          <Panel eyebrow={`Scenario ${latest.scenario_id}`} title="Ranked Alternatives" className="mb-5">
            <div className="grid grid-cols-1 gap-3">
              {latest.ranked_options.map((opt: ProcurementOption, idx: number) => (
                <div
                  key={opt.supplier_id}
                  className="flex items-center justify-between px-4 py-3 rounded-sm border border-[var(--color-hairline)] bg-[var(--color-hull-raised)]"
                >
                  <div className="flex items-center gap-4">
                    <div className="font-display text-lg text-[var(--color-phosphor)] w-6">#{idx + 1}</div>
                    <div>
                      <div className="text-sm font-medium">{opt.country} — {opt.crude_grade}</div>
                      <div className="text-xs text-[var(--color-ink-muted)] mt-0.5">
                        via {opt.primary_corridor.replace(/_/g, " ")} · route risk {opt.route_risk}
                        {opt.sanctions_status !== "none" && ` · ${opt.sanctions_status.replace(/_/g, " ")}`}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="font-display text-[10px] text-[var(--color-ink-faint)] uppercase">Cost delta</div>
                      <div className="font-display text-sm tabular-nums">{opt.cost_usd_bbl >= 0 ? "+" : ""}{opt.cost_usd_bbl} $/bbl</div>
                    </div>
                    <div className="text-right">
                      <div className="font-display text-[10px] text-[var(--color-ink-faint)] uppercase">ETA</div>
                      <div className="font-display text-sm tabular-nums">{opt.delay_days}d</div>
                    </div>
                    <div className="text-right">
                      <div className="font-display text-[10px] text-[var(--color-ink-faint)] uppercase">Allocation</div>
                      <div className="font-display text-sm tabular-nums">{opt.recommended_allocation_mbd} mbd</div>
                    </div>
                    <Button variant={idx === 0 ? "primary" : "ghost"}
                      disabled={executing === latest.id || opt.recommended_allocation_mbd === 0}
                      onClick={() => execute(latest.id)}>
                      Execute
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 font-display text-[11px] text-[var(--color-ink-faint)]">
              Combined demand coverage: {latest.ranked_options[0]?.total_demand_coverage_pct ?? "—"}% of the forecast supply gap
            </div>
          </Panel>

          {confirmation && (
            <Panel eyebrow="Confirmation" title="Procurement Order" className="border-[var(--color-phosphor)]/40">
              <pre className="font-display text-xs text-[var(--color-ink-muted)] whitespace-pre-wrap">
                {JSON.stringify(confirmation, null, 2)}
              </pre>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
