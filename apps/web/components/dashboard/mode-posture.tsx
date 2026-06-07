import type { ModeName } from "@/lib/dashboard";

type Props = {
  systemMode: ModeName;
};

const MODES: { value: ModeName; label: string }[] = [
  { value: "normal", label: "Normal" },
  { value: "degraded", label: "Degraded" },
  { value: "blackout", label: "Blackout" }
];

export function ModePosture({ systemMode }: Props) {
  return (
    <div className="persona-switch" aria-label="Live system mode">
      <span className="persona-switch-label">Mode</span>
      <div className="persona-switch-options">
        {MODES.map((mode) => {
          const active = mode.value === systemMode;
          const className = active
            ? `persona-option mode-option active mode-${mode.value}`
            : "persona-option mode-option";
          return (
            <span key={mode.value} className={className} aria-current={active ? "true" : undefined}>
              {mode.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
