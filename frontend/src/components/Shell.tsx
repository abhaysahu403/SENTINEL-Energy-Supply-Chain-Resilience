import { NavLink } from "react-router-dom";
import { Activity, Ship, Radio, Fuel, Database, GitBranch } from "lucide-react";
import type { ReactNode } from "react";

const NAV = [
  { to: "/", label: "War Room", icon: Radio },
  { to: "/simulator", label: "Scenario Simulator", icon: Activity },
  { to: "/procurement", label: "Procurement Console", icon: Ship },
  { to: "/reserves", label: "Reserve Planner", icon: Fuel },
  { to: "/trace", label: "Agent Trace", icon: GitBranch },
];

export function Shell({ children, connected }: { children: ReactNode; connected: boolean }) {
  return (
    <div className="min-h-screen bg-[var(--color-abyss)] bg-ops-grid flex">
      <aside className="w-60 shrink-0 border-r border-[var(--color-hairline)] bg-[var(--color-hull)] flex flex-col">
        <div className="px-5 py-5 border-b border-[var(--color-hairline)]">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-[var(--color-phosphor)]" />
            <span className="font-display text-sm tracking-[0.2em] text-[var(--color-ink-bright)]">SENTINEL</span>
          </div>
          <div className="font-display text-[9px] tracking-[0.14em] text-[var(--color-ink-faint)] mt-1 uppercase">
            Energy Supply Chain Resilience
          </div>
        </div>

        <nav className="flex-1 py-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-5 py-2.5 text-sm border-l-2 transition-colors ${
                  isActive
                    ? "border-[var(--color-phosphor)] text-[var(--color-phosphor)] bg-[var(--color-phosphor-glow)]"
                    : "border-transparent text-[var(--color-ink-muted)] hover:text-[var(--color-ink-bright)] hover:bg-[var(--color-hull-raised)]"
                }`
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-[var(--color-hairline)] flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full rounded-full ${connected ? "bg-[var(--color-risk-low)]" : "bg-[var(--color-risk-critical)]"} opacity-75 ${connected ? "animate-ping" : ""}`}
            />
            <span className={`relative inline-flex rounded-full h-2 w-2 ${connected ? "bg-[var(--color-risk-low)]" : "bg-[var(--color-risk-critical)]"}`} />
          </span>
          <span className="font-display text-[10px] tracking-[0.1em] text-[var(--color-ink-faint)] uppercase">
            {connected ? "Live feed connected" : "Reconnecting…"}
          </span>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
