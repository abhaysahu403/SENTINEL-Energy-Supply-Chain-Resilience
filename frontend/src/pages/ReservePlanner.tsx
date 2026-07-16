import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip,
} from "recharts";
import { Panel, StatReadout } from "../components/ui";
import { api } from "../api/client";
import type { ReserveStatus } from "../types";

export function ReservePlanner() {
  const [status, setStatus] = useState<ReserveStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.getReserveStatus().then(setStatus).catch(() => setError(true));
  }, []);

  const chartData = status?.schedule?.schedule?.map((s) => ({
    day: `Day ${s.day + 1}`,
    drawdown: s.drawdown_mb,
  })) ?? [];

  return (
    <div className="p-6 max-w-[1400px]">
      <h1 className="font-display text-lg tracking-[0.08em] mb-0.5">STRATEGIC RESERVE PLANNER</h1>
      <p className="text-sm text-[var(--color-ink-muted)] mb-6">
        LP-optimized SPR drawdown schedule against forecast supply gaps, respecting the floor reserve.
      </p>

      {error && (
        <Panel className="text-sm text-[var(--color-ink-faint)] font-display py-10 text-center">
          No reserve simulation yet — run a scenario in the Simulator and select "View reserve impact."
        </Panel>
      )}

      {status && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-5">
            <Panel><StatReadout label="Days of Cover" value={status.days_of_cover} unit="days" tone="risk-high" /></Panel>
            <Panel><StatReadout label="Recommended Daily Drawdown" value={status.recommended_drawdown_mbd} unit="mb/day" tone="phosphor" /></Panel>
            <Panel><StatReadout label="Gap Coverage" value={status.schedule.gap_coverage_pct} unit="%" tone={status.schedule.gap_coverage_pct >= 90 ? "risk-low" : "risk-med"} /></Panel>
            <Panel><StatReadout label="Floor Reserve" value={status.schedule.floor_reserve_mb} unit="mb" tone="default" /></Panel>
          </div>

          <Panel eyebrow="Drawdown Schedule" title="Daily Recommended Release">
            <div style={{ width: "100%", height: 280 }}>
              <ResponsiveContainer>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="drawdownFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ffb000" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#ffb000" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#232c3a" strokeDasharray="3 3" />
                  <XAxis dataKey="day" stroke="#545e70" tick={{ fontSize: 10, fontFamily: "monospace" }} />
                  <YAxis stroke="#545e70" tick={{ fontSize: 10, fontFamily: "monospace" }} />
                  <RTooltip
                    contentStyle={{ background: "#161d28", border: "1px solid #232c3a", fontSize: 12, fontFamily: "monospace" }}
                  />
                  <Area type="monotone" dataKey="drawdown" stroke="#ffb000" fill="url(#drawdownFill)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel eyebrow="Explainability" title="Optimization Assumptions" className="mt-5">
            <div className="font-display text-xs text-[var(--color-ink-muted)] flex flex-col gap-1.5">
              <div>floor_reserve_pct = {status.schedule.assumptions.floor_reserve_pct}% — SPR is never drawn below this fraction of total capacity</div>
              <div>max_daily_drawdown_mbd = {status.schedule.assumptions.max_daily_drawdown_mbd} — physical cavern/pipeline withdrawal ceiling per day</div>
              <div>Solver status: <span className="text-[var(--color-phosphor)]">{status.schedule.solver_status}</span></div>
              <div>Available above floor: {status.schedule.available_above_floor_mb} mb of {status.schedule.total_forecast_gap_mb} mb forecast gap</div>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
