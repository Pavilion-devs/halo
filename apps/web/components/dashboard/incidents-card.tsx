import Link from "next/link";

import type { Incident } from "@/lib/api";
import type { ModeName } from "@/lib/dashboard";
import { prettyStage } from "@/lib/dashboard";

type Props = {
  incidents: Incident[];
};

const MODE_TONE: Record<ModeName, string> = {
  normal: "green",
  degraded: "amber",
  blackout: "pink"
};

const TargetIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Incident</title>
    <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.8" />
    <path d="M8 12h8M12 8v8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const PlusIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>All</title>
    <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

const ellipsis = {
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap" as const
};

export function IncidentsCard({ incidents }: Props) {
  return (
    <div className="card c-project">
      <div className="plist-head">
        <h3>Incidents</h3>
        <Link href="/incidents" className="plist-new">
          <PlusIcon />
          View all
        </Link>
      </div>

      {incidents.length === 0 ? (
        <div className="empty-state">
          <strong>No active incidents</strong>
          Incidents appear here the moment Halo accepts a trigger into the workflow.
        </div>
      ) : (
        <div className="plist">
          {incidents.slice(0, 5).map((incident) => (
            <Link
              key={incident.id}
              href={`/incidents/${incident.id}`}
              className="p-item"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div className={`p-ic ${MODE_TONE[incident.mode]}`}>
                <TargetIcon />
              </div>
              <div className="p-body" style={{ minWidth: 0 }}>
                <div className="p-name" style={ellipsis}>
                  {incident.title}
                </div>
                <div className="p-meta" style={ellipsis}>
                  {incident.severity.toUpperCase()} · {prettyStage(incident.stage)} · cp{" "}
                  {incident.checkpoint_index}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
