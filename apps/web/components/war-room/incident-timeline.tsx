import type { IncidentEvent } from "@/lib/api";
import { prettyEventType, relativeTime } from "@/lib/dashboard";
import { eventSummary, eventTone, TONE_PILL, type EventTone } from "@/lib/war-room";

type Props = {
  events: IncidentEvent[];
};

const PILL_LABEL: Record<EventTone, string> = {
  ok: "ok",
  warn: "watch",
  bad: "fail",
  info: "info"
};

export function IncidentTimeline({ events }: Props) {
  const ordered = [...events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="card c-launches-full wr-timeline">
      <div className="list-head">
        <h3>Event timeline</h3>
        <span className="count-pill muted">
          {events.length} event{events.length === 1 ? "" : "s"}
        </span>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <strong>No events yet</strong>
          Run the workflow from the operator console to populate the timeline.
        </div>
      ) : (
        <div className="list-rows">
          {ordered.map((event) => {
            const tone = eventTone(event);
            return (
              <div key={event.id} className="launch-row" style={{ cursor: "default" }}>
                <div className="l-avatar">
                  {prettyEventType(event.type).charAt(0)}
                </div>
                <div className="l-body">
                  <div className="l-name">{prettyEventType(event.type)}</div>
                  <div className="l-meta">{eventSummary(event)}</div>
                </div>
                <div className="l-metrics">
                  <span className={TONE_PILL[tone]}>{PILL_LABEL[tone]}</span>
                  <span style={{ fontSize: 12, color: "var(--ink-dim)" }}>
                    {relativeTime(event.created_at)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
