import { AlertTriangle, Info } from "lucide-react";
import type { AlertPayload } from "../types";

export interface FeedItem extends AlertPayload {
  id: string;
  receivedAt: number;
}

export function AlertFeed({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return (
      <div className="text-sm text-[var(--color-ink-faint)] font-display py-6 text-center">
        No signals yet — awaiting live feed…
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2 max-h-[520px] overflow-y-auto pr-1">
      {items.map((item) => {
        const critical = item.level === "critical";
        return (
          <div
            key={item.id}
            className={`flex gap-2.5 items-start px-3 py-2.5 rounded-sm border text-sm ${
              critical
                ? "border-[var(--color-risk-critical)]/40 bg-[var(--color-risk-critical)]/10"
                : "border-[var(--color-hairline)] bg-[var(--color-hull-raised)]"
            }`}
          >
            {critical
              ? <AlertTriangle size={15} className="shrink-0 mt-0.5 text-[var(--color-risk-critical)]" />
              : <Info size={15} className="shrink-0 mt-0.5 text-[var(--color-ink-faint)]" />}
            <div className="min-w-0">
              <div className={critical ? "text-[var(--color-ink-bright)]" : "text-[var(--color-ink-muted)]"}>
                {item.message}
              </div>
              <div className="font-display text-[10px] text-[var(--color-ink-faint)] mt-1">
                {new Date(item.receivedAt).toLocaleTimeString()} · trace {item.trace_id.slice(0, 12)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
