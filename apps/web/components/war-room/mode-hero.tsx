import type { ModeName } from "@/lib/dashboard";

type Props = {
  mode: ModeName;
  agent: string;
};

const MODE_COPY: Record<ModeName, string> = {
  normal: "Full autonomy · best model · all tools",
  degraded: "Fallback route · read-heavy · tighter loops",
  blackout: "No risky writes · preserve state · handoff"
};

export function ModeHero({ mode, agent }: Props) {
  return (
    <div className={`card dark stat c-stat-1 mode-hero mode-${mode}`}>
      <div className="stat-head">
        <div className="stat-title">Operating mode</div>
        <span className={`mode-dot mode-${mode}`} style={{ marginTop: 8 }} />
      </div>
      <div className="mode-hero-value">{mode.charAt(0).toUpperCase() + mode.slice(1)}</div>
      <div className="stat-foot">{agent}</div>
      <div className="mode-hero-copy">{MODE_COPY[mode]}</div>
    </div>
  );
}
