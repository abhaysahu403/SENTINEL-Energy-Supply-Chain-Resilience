import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Panel, StatReadout, Button } from "../components/ui";
import { api } from "../api/client";
import type { ScenarioTemplate, Scenario } from "../types";

export function ScenarioSimulator() {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [volumeLossPct, setVolumeLossPct] = useState<number>(50);
  const [durationDays, setDurationDays] = useState<number>(14);
  const [result, setResult] = useState<Scenario | null>(null);
  const [running, setRunning] = useState(false);
  const [showAssumptions, setShowAssumptions] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.getScenarioTemplates().then((t) => {
      setTemplates(t);
      if (t.length) {
        setSelected(t[0].template_id);
        setVolumeLossPct(t[0].default_volume_loss_pct);
        setDurationDays(t[0].default_duration_days);
      }
    });
  }, []);

  function onSelectTemplate(id: string) {
    setSelected(id);
    const t = templates.find((x) => x.template_id === id);
    if (t) {
      setVolumeLossPct(t.default_volume_loss_pct);
      setDurationDays(t.default_duration_days);
    }
    setResult(null);
  }

  async function runSimulation() {
    setRunning(true);
    try {
      const r = await api.runScenario(selected, { volume_loss_pct: volumeLossPct, duration_days: durationDays });
      setResult(r);
    } finally {
      setRunning(false);
    }
  }

  async function proceedToProcurement() {
    if (!result) return;
    await api.generateProcurement(result.id);
    navigate(`/procurement?scenario_id=${result.id}`);
  }

  async function proceedToReserves() {
    if (!result) return;
    await api.simulateReserve(result.id);
    navigate("/reserves");
  }

  return (
    <div className="p-6 max-w-[1500px]">
      <h1 className="font-display text-lg tracking-[0.08em] mb-0.5">SCENARIO SIMULATOR</h1>
      <p className="text-sm text-[var(--color-ink-muted)] mb-6">
        Model a disruption event and see its cascading impact — every number below shows the formula that produced it.
      </p>

      <div className="grid grid-cols-3 gap-5">
        <Panel eyebrow="Configure" title="Disruption Scenario">
          <div className="flex flex-col gap-4">
            <div>
              <label className="font-display text-[10px] tracking-[0.1em] text-[var(--color-ink-faint)] uppercase block mb-1.5">
                Scenario Template
              </label>
              <select
                value={selected}
                onChange={(e) => onSelectTemplate(e.target.value)}
                className="w-full bg-[var(--color-hull-raised)] border border-[var(--color-hairline)] rounded-sm px-3 py-2 text-sm"
              >
                {templates.map((t) => (
                  <option key={t.template_id} value={t.template_id}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-display text-[10px] tracking-[0.1em] text-[var(--color-ink-faint)] uppercase block mb-1.5">
                Volume Loss — {volumeLossPct}%
              </label>
              <input type="range" min={5} max={100} value={volumeLossPct}
                onChange={(e) => setVolumeLossPct(Number(e.target.value))}
                className="w-full accent-[var(--color-phosphor)]" />
            </div>

            <div>
              <label className="font-display text-[10px] tracking-[0.1em] text-[var(--color-ink-faint)] uppercase block mb-1.5">
                Duration — {durationDays} days
              </label>
              <input type="range" min={1} max={90} value={durationDays}
                onChange={(e) => setDurationDays(Number(e.target.value))}
                className="w-full accent-[var(--color-phosphor)]" />
            </div>

            <Button onClick={runSimulation} disabled={running || !selected}>
              {running ? "Running simulation…" : "Run simulation"}
            </Button>
          </div>
        </Panel>

        <div className="col-span-2 flex flex-col gap-5">
          {!result && (
            <Panel className="flex items-center justify-center h-64 text-[var(--color-ink-faint)] text-sm font-display">
              Configure a scenario and run it to see the cascade.
            </Panel>
          )}

          {result && (
            <>
              <div className="grid grid-cols-3 gap-4">
                <Panel>
                  <StatReadout label="India Supply Gap" value={result.results.volume_lost_mbd} unit="mbd" tone="risk-high" />
                </Panel>
                <Panel>
                  <StatReadout label="Fuel Price Impact" value={`+${result.results.fuel_price_delta_pct}`} unit="%" tone="risk-med" />
                </Panel>
                <Panel>
                  <StatReadout label="GDP Growth Impact" value={result.results.gdp_impact.gdp_growth_delta_pp} unit="pp" tone="risk-critical" />
                </Panel>
              </div>

              <Panel eyebrow="Cascade — Refinery Impact" title="Run-Rate Delta by Refinery">
                <div className="flex flex-col gap-2">
                  {result.results.refinery_impacts.map((r) => (
                    <div key={r.refinery_id} className="flex items-center gap-3">
                      <div className="w-40 text-sm text-[var(--color-ink-muted)] shrink-0">{r.name}</div>
                      <div className="flex-1 h-5 bg-[var(--color-hull-raised)] rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-[var(--color-risk-high)]"
                          style={{ width: `${Math.min(100, Math.abs(r.run_rate_delta_pct))}%` }}
                        />
                      </div>
                      <div className="font-display text-xs w-14 text-right tabular-nums text-[var(--color-risk-high)]">
                        {r.run_rate_delta_pct}%
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel eyebrow="Cascade — Downstream" title="Power Sector & Macro">
                <div className="grid grid-cols-2 gap-4">
                  <StatReadout label="Diesel Substitution (Power Sector)"
                    value={`+${result.results.power_sector.diesel_substitution_delta_pp}`} unit="pp" />
                  <StatReadout label="Implied Brent Shock"
                    value={`+${result.results.gdp_impact.implied_brent_usd_shock}`} unit="USD/bbl" />
                </div>
              </Panel>

              <Panel
                eyebrow="Explainability"
                title="Assumptions Used"
                right={
                  <button
                    className="font-display text-[10px] text-[var(--color-phosphor)] uppercase tracking-[0.08em]"
                    onClick={() => setShowAssumptions((s) => !s)}
                  >
                    {showAssumptions ? "Hide" : "Show your work"}
                  </button>
                }
              >
                {showAssumptions ? (
                  <div className="font-display text-xs text-[var(--color-ink-muted)] flex flex-col gap-1.5">
                    <div>fuel_price_elasticity_to_crude = {result.results.assumptions_used.fuel_price_elasticity_to_crude} — 1% crude cost rise passes through as this fraction of a % rise in retail fuel price over {result.results.retail_pass_through_days} days</div>
                    <div>power_sector_diesel_substitution_pct_per_10pct_gas_shortfall = {result.results.assumptions_used.power_sector_diesel_substitution_pct_per_10pct_gas_shortfall}</div>
                    <div>gdp_elasticity_to_10usd_oil_shock = {result.results.assumptions_used.gdp_elasticity_to_10usd_oil_shock} — GDP growth (pp) impact per $10/bbl sustained shock</div>
                    <div className="text-[var(--color-ink-faint)] mt-1">
                      All coefficients are adjustable in app/agents/assumptions.py and sourced from public IMF/RBI/PPAC studies (order-of-magnitude estimates, not point forecasts).
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-[var(--color-ink-faint)]">
                    Click "Show your work" to see exactly which coefficients produced every number above.
                  </div>
                )}
              </Panel>

              <div className="flex gap-3">
                <Button onClick={proceedToProcurement}>View procurement options →</Button>
                <Button variant="ghost" onClick={proceedToReserves}>View reserve impact →</Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
