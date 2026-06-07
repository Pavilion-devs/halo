import Link from "next/link";

import type { Incident } from "@/lib/api";
import { prettyStage, relativeTime } from "@/lib/dashboard";

type Props = {
  incident: Incident | null;
};

const Dots = () => (
  <svg width={16} height={16} viewBox="0 0 24 24" fill="none">
    <title>More</title>
    <circle cx="5" cy="12" r="1.5" fill="currentColor" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    <circle cx="19" cy="12" r="1.5" fill="currentColor" />
  </svg>
);

const ClockIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Time</title>
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
    <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const OpenIcon = () => (
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

export function ActiveIncidentCard({ incident }: Props) {
  return (
    <div className="card c-reminder">
      <div className="rem-head">
        <h4>Active incident</h4>
        <span className="more">
          <Dots />
        </span>
      </div>
      {incident ? (
        <>
          <div className="rem-title">{incident.title}</div>
          <div className="rem-time">
            <span className={`mode-dot mode-${incident.mode}`} />
            {incident.mode} · {prettyStage(incident.stage)} · {relativeTime(incident.updated_at)}
          </div>
          <Link href={`/incidents/${incident.id}`} className="rem-btn" style={{ textDecoration: "none" }}>
            <OpenIcon />
            Open war room
          </Link>
        </>
      ) : (
        <>
          <div className="rem-title">
            All clear
            <br />
            no active incident
          </div>
          <div className="rem-time">
            <ClockIcon />
            Halo is watching for the next trigger
          </div>
          <button className="rem-btn" type="button" disabled>
            <OpenIcon />
            Standing by
          </button>
        </>
      )}
    </div>
  );
}
