import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Panel, StatReadout, RiskPill, Button } from "../components/ui";
import { CorridorMap } from "../components/CorridorMap";
import { AlertFeed, type FeedItem } from "../components/AlertFeed";
import { api } from "../api/client";
import type { Corridor } from "../types";
import type { LiveMessage } from "../hooks/useLiveFeed";

export function Dashboard({ lastMessage }: { lastMessage: LiveMessage | null }) {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [injecting, setInjecting] = useState(false);
  const navigate = useNavigate();

  const refresh = useCallback(() => {
    api.getCorridors().then(setCorridors).catch(() => {});
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === "risk_update") {
      setCorridors((prev) =>
        prev.map((c) => c.id === lastMessage.payload.corridor_id
          ? { ...c, current_risk_score: lastMessage.payload.score }
          : c)
      );
    }
    if (lastMessage.type === "alert") {
      setFeed((prev) => [
        { ...lastMessage.payload, id: `${Date.now()}_${Math.random()}`, receivedAt: Date.now() },
        ...prev,
      ].slice(0, 40));
    }
  }, [lastMessage]);

  const nationalRiskIndex = corridors.length
    ? Math.round(corridors.reduce((s, c) => s + c.current_risk_score, 0) / corridors.length)
    : 0;
  const hormuz = corridors.find((c) => c.id === "hormuz");

  async function injectDemoEvent() {
    setInjecting(true);
    try {
      await api.injectEvent({
        headline: "Naval escalation reported in Strait of Hormuz",
        raw_text: "A significant naval escalation involving multiple vessels has been reported transiting the Strait of Hormuz, sharply raising transit risk for tankers.",
        event_type: "military_standoff",
        affected_corridor: "hormuz",
        affected_suppliers: ["iraq", "saudi_arabia", "uae"],
        severity: 93,
      });
    } finally {
      setTimeout(() => setInjecting(false), 2000);
    }
  }

  return (
    <div className="p-6 max-w-[1600px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-lg tracking-[0.08em] text-[var(--color-ink-bright)]">WAR ROOM</h1>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            Live geopolitical & logistics risk across India's crude import corridors
          </p>
        </div>
        <Button onClick={injectDemoEvent} disabled={injecting}>
          {injecting ? "Signal injected — watch the feed…" : "Inject test disruption signal"}
        </Button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-5">
        <Panel>
          <StatReadout label="National Risk Index" value={nationalRiskIndex} unit="/100"
            tone={nationalRiskIndex >= 45 ? "risk-high" : "phosphor"} />
        </Panel>
        <Panel>
          <StatReadout label="Hormuz Corridor Risk" value={hormuz ? hormuz.current_risk_score.toFixed(1) : "—"}
            tone="risk-med" />
        </Panel>
        <Panel>
          <StatReadout label="SPR Days-of-Cover" value="9.5" unit="days" tone="risk-high" />
        </Panel>
        <Panel>
          <StatReadout label="Import Dependency" value="88" unit="%" tone="default" />
        </Panel>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <Panel eyebrow="Digital Twin" title="Global Corridor Risk Map" className="col-span-2 h-[560px] flex flex-col">
          <div className="flex-1 -m-4 mt-0">
            <CorridorMap corridors={corridors} />
          </div>
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel eyebrow="Live Signal Feed" title="Alerts">
            <AlertFeed items={feed} />
          </Panel>
        </div>
      </div>

      <Panel eyebrow="Corridor Status" title="All Monitored Corridors" className="mt-5">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--color-ink-faint)] font-display text-[10px] tracking-[0.1em] uppercase">
              <th className="pb-2 font-normal">Corridor</th>
              <th className="pb-2 font-normal">India Dependency</th>
              <th className="pb-2 font-normal">Baseline Volume</th>
              <th className="pb-2 font-normal">Status</th>
              <th className="pb-2 font-normal"></th>
            </tr>
          </thead>
          <tbody>
            {corridors.map((c) => (
              <tr key={c.id} className="border-t border-[var(--color-hairline)]">
                <td className="py-2.5">{c.name}</td>
                <td className="py-2.5 text-[var(--color-ink-muted)]">{c.india_dependency_pct}%</td>
                <td className="py-2.5 text-[var(--color-ink-muted)]">{c.baseline_daily_volume_mbd} mbd</td>
                <td className="py-2.5"><RiskPill score={c.current_risk_score} /></td>
                <td className="py-2.5 text-right">
                  <button
                    className="font-display text-[10px] tracking-[0.08em] uppercase text-[var(--color-phosphor)] hover:underline"
                    onClick={() => navigate("/simulator")}
                  >
                    Simulate →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
