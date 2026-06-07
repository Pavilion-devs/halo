import type { ReactNode } from "react";

type StatCardProps = {
  title: string;
  value: ReactNode;
  footIcon: ReactNode;
  footText: ReactNode;
  variant: "stat-1" | "stat-2" | "stat-3" | "stat-4";
  dark?: boolean;
};

const ArrowUpRight = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Open</title>
    <path
      d="M7 17 17 7M8 7h9v9"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export function StatCard({ title, value, footIcon, footText, variant, dark }: StatCardProps) {
  const classes = ["card", "stat", dark ? "dark" : "", `c-${variant}`].filter(Boolean).join(" ");
  return (
    <div className={classes}>
      <div className="stat-head">
        <div className="stat-title">{title}</div>
        <div className="stat-arrow">
          <ArrowUpRight />
        </div>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-foot">
        {footIcon}
        {footText}
      </div>
    </div>
  );
}
