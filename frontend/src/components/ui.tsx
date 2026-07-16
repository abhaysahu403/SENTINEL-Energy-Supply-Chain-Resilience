import type { ReactNode } from "react";

export function riskColor(score: number): string {
  if (score >= 65) return "var(--color-risk-critical)";
  if (score >= 45) return "var(--color-risk-high)";
  if (score >= 25) return "var(--color-risk-med)";
  return "var(--color-risk-low)";
}

export function riskLabel(score: number): string {
  if (score >= 65) return "CRITICAL";
  if (score >= 45) return "ELEVATED";
  if (score >= 25) return "WATCH";
  return "NOMINAL";
}

export function Panel({ title, eyebrow, children, className = "", right }: {
  title?: string; eyebrow?: string; children: ReactNode; className?: string; right?: ReactNode;
}) {
  return (
    <div className={`bg-[var(--color-hull)] border border-[var(--color-hairline)] rounded-sm ${className}`}>
      {(title || eyebrow) && (
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--color-hairline)]">
          <div>
            {eyebrow && (
              <div className="font-display text-[10px] tracking-[0.18em] text-[var(--color-ink-faint)] uppercase">
                {eyebrow}
              </div>
            )}
            {title && <div className="text-sm font-medium text-[var(--color-ink-bright)]">{title}</div>}
          </div>
          {right}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

export function StatReadout({ label, value, unit, tone = "default" }: {
  label: string; value: string | number; unit?: string;
  tone?: "default" | "phosphor" | "risk-critical" | "risk-high" | "risk-med" | "risk-low";
}) {
  const toneColor: Record<string, string> = {
    default: "var(--color-ink-bright)",
    phosphor: "var(--color-phosphor)",
    "risk-critical": "var(--color-risk-critical)",
    "risk-high": "var(--color-risk-high)",
    "risk-med": "var(--color-risk-med)",
    "risk-low": "var(--color-risk-low)",
  };
  return (
    <div>
      <div className="font-display text-[10px] tracking-[0.14em] text-[var(--color-ink-faint)] uppercase mb-1">
        {label}
      </div>
      <div className="font-display text-2xl tabular-nums" style={{ color: toneColor[tone] }}>
        {value}{unit && <span className="text-sm text-[var(--color-ink-muted)] ml-1">{unit}</span>}
      </div>
    </div>
  );
}

export function RiskPill({ score }: { score: number }) {
  const color = riskColor(score);
  return (
    <span
      className="font-display text-[10px] tracking-[0.1em] px-2 py-0.5 rounded-sm border"
      style={{ color, borderColor: color, backgroundColor: `${color}1a` }}
    >
      {riskLabel(score)} · {score.toFixed(1)}
    </span>
  );
}

export function Button({ children, onClick, variant = "primary", disabled, className = "" }: {
  children: ReactNode; onClick?: () => void; variant?: "primary" | "ghost"; disabled?: boolean; className?: string;
}) {
  const base = "font-display text-xs tracking-[0.06em] uppercase px-3.5 py-2 rounded-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed";
  const styles = variant === "primary"
    ? "bg-[var(--color-phosphor)] text-[#1a1200] hover:brightness-110"
    : "border border-[var(--color-hairline)] text-[var(--color-ink-muted)] hover:text-[var(--color-ink-bright)] hover:border-[var(--color-ink-faint)]";
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${styles} ${className}`}>
      {children}
    </button>
  );
}
