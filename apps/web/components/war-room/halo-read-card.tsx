import type { Incident } from "@/lib/api";
import { relativeTime } from "@/lib/dashboard";
import { splitRecommendation } from "@/lib/markdown";
import { parseRecommendation } from "@/lib/war-room";

import { MarkdownView } from "./markdown-view";

type Props = {
  incident: Incident;
};

export function HaloReadCard({ incident }: Props) {
  const { preparedActions } = parseRecommendation(incident.latest_recommendation);
  const blocks = splitRecommendation(incident.latest_recommendation);

  return (
    <div className="card c-conviction">
      <div className="list-head">
        <h3>Halo&apos;s read</h3>
        <span className="count-pill muted">{incident.mode} lens</span>
      </div>

      <div className="memo-panel">
        <div className="memo-convo">
          <div className="memo-prose-block">
            <span className="memo-mini-label">situation</span>
            <p className="memo-prose">
              {incident.summary ?? "Halo has not written an incident summary yet."}
            </p>
          </div>

          {incident.last_failure ? (
            <div className="memo-prose-block">
              <span className="memo-mini-label">last failure caught</span>
              <p className="memo-prose">{incident.last_failure}</p>
            </div>
          ) : null}

          {blocks.length > 0 ? (
            <MarkdownView blocks={blocks} />
          ) : (
            <p className="memo-prose memo-empty">
              Run the next workflow step to get Halo&apos;s recommendation.
            </p>
          )}

          {preparedActions.length > 0 ? (
            <div className="prepared-action-strip">
              {preparedActions.map((action) => (
                <div key={action.id} className="prepared-action-chip">
                  <span>{action.name}</span>
                  <b className="mono">{action.id}</b>
                  <em>{action.status ?? "Prepared"}</em>
                </div>
              ))}
            </div>
          ) : null}

          <div className="memo-convo-footer">
            <span className="memo-foot-item">
              {incident.current_agent} · {incident.current_virtual_model}
            </span>
            <span className="memo-foot-item">
              {incident.fallback_action ??
                "normal posture: full model route and all configured Jaguar tools"}
            </span>
            <span className="memo-foot-item">updated {relativeTime(incident.updated_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
