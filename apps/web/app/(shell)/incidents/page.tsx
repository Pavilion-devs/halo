import Link from "next/link";

import { getIncidents } from "@/lib/api";
import type { ModeName } from "@/lib/dashboard";
import { prettyStage, relativeTime } from "@/lib/dashboard";

export const dynamic = "force-dynamic";

const MODE_PILL: Record<ModeName, string> = {
  normal: "enter",
  degraded: "watch",
  blackout: "ignore"
};

const MODE_AVATAR: Record<ModeName, string> = {
  normal: "",
  degraded: "tone-amber",
  blackout: "tone-pink"
};

export default async function IncidentsPage() {
  const { incidents, error } = await getIncidents();
  const sorted = [...incidents].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Incidents</h1>
          <div className="sub">Every incident Halo is commanding or has handed off.</div>
        </div>
      </div>

      <div className="dash-grid">
        <div className="card c-launches-full">
          <div className="list-head">
            <h3>All incidents</h3>
            <span className="count-pill muted">{incidents.length} total</span>
          </div>

          {incidents.length === 0 ? (
            <div className="empty-state">
              <strong>No incidents yet</strong>
              {error ?? "Create an incident through the Halo API to populate this list."}
            </div>
          ) : (
            <div className="list-rows">
              {sorted.map((incident) => (
                <Link key={incident.id} href={`/incidents/${incident.id}`} className="launch-row">
                  <div className={`l-avatar ${MODE_AVATAR[incident.mode]}`}>
                    {incident.severity.slice(3)}
                  </div>
                  <div className="l-body">
                    <div className="l-name">{incident.title}</div>
                    <div className="l-meta">
                      {incident.product}/{incident.environment} · {prettyStage(incident.stage)} · cp{" "}
                      {incident.checkpoint_index}
                    </div>
                  </div>
                  <div className="l-metrics">
                    <span className={`verdict-pill ${MODE_PILL[incident.mode]}`}>
                      {incident.mode}
                    </span>
                    <span style={{ fontSize: 12, color: "var(--ink-dim)" }}>
                      {relativeTime(incident.updated_at)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
