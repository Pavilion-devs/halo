import Link from "next/link";

import type { ModeName, RecentEvent } from "@/lib/dashboard";
import { prettyEventType, relativeTime } from "@/lib/dashboard";

type Props = {
  events: RecentEvent[];
};

const MODE_PILL: Record<ModeName, { className: string; label: string }> = {
  normal: { className: "completed", label: "Normal" },
  degraded: { className: "progress", label: "Degraded" },
  blackout: { className: "pending", label: "Blackout" }
};

const MODE_AVATAR: Record<ModeName, string> = {
  normal: "var(--evt-av-normal, linear-gradient(135deg, #2ea86b, #14593a))",
  degraded: "var(--evt-av-degraded, linear-gradient(135deg, #e8b75a, #c2871a))",
  blackout: "var(--evt-av-blackout, linear-gradient(135deg, #e58597, #b8475f))"
};

export function RecentEventsCard({ events }: Props) {
  return (
    <div className="card c-team">
      <div className="team-head">
        <h3>Recent activity</h3>
        <Link href="/incidents" className="add-member" style={{ textDecoration: "none" }}>
          See all →
        </Link>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <strong>No activity yet</strong>
          Workflow events stream here as Halo classifies, gathers evidence, and recovers.
        </div>
      ) : (
        <div className="team-list">
          {events.slice(0, 4).map((event) => {
            const mode = (event.mode ?? "normal") as ModeName;
            const pill = MODE_PILL[mode];
            return (
              <Link
                key={event.id}
                href={`/incidents/${event.incidentId}`}
                className="team-row"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div className="t-avatar" style={{ background: MODE_AVATAR[mode] }}>
                  {mode.charAt(0).toUpperCase()}
                </div>
                <div className="t-body" style={{ minWidth: 0 }}>
                  <div className="t-name">{prettyEventType(event.type)}</div>
                  <div
                    className="t-task"
                    style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  >
                    {event.incidentTitle} · {relativeTime(event.createdAt)}
                  </div>
                </div>
                <span className={`status-pill ${pill.className}`}>{pill.label}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
