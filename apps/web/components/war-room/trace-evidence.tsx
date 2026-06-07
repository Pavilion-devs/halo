import type { TraceView } from "@/lib/war-room";
import { shortModel } from "@/lib/war-room";

type Props = {
  traces: TraceView[];
};

export function TraceEvidence({ traces }: Props) {
  const toolSummary = summarizeTools(traces);

  return (
    <div className="card c-conviction">
      <div className="list-head">
        <h3>Trace evidence</h3>
        <span className="count-pill muted">
          {traces.length} trace{traces.length === 1 ? "" : "s"}
        </span>
      </div>

      {traces.length === 0 ? (
        <div className="empty-state">
          <strong>No traces yet</strong>
          TrueFoundry trace IDs land here as Halo invokes the Bedrock-backed agent.
        </div>
      ) : (
        <div className="trace-list">
          {traces.map((trace) => {
            const live = trace.status !== null || trace.spanCount !== null;
            const guardrailOnly = trace.guardrails.length > 0 && !trace.failure;
            const statusClass = trace.failure ? "ignore" : guardrailOnly ? "guardrail" : "enter";
            const label = trace.failure
              ? "failed"
              : guardrailOnly
                ? "guardrail event"
                : trace.status ?? trace.lookupStatus;
            return (
              <div key={trace.traceId} className="trace-card">
                <div className="trace-top">
                  <span className="trace-id mono">{trace.traceId.slice(0, 20)}…</span>
                  <span className={`verdict-pill ${live ? statusClass : "watch"}`}>
                    {label}
                  </span>
                </div>

                {live ? (
                  <div className="trace-kv">
                    <div className="trace-kv-cell">
                      <span>model</span>
                      <b className="mono">{shortModel(trace.modelName)}</b>
                    </div>
                    <div className="trace-kv-cell">
                      <span>spans</span>
                      <b className="mono">{trace.spanCount ?? "—"}</b>
                    </div>
                    <div className="trace-kv-cell wide">
                      <span>root span</span>
                      <b className="mono">{trace.rootSpanName ?? "—"}</b>
                    </div>
                  </div>
                ) : (
                  <div className="trace-pending">
                    Pending ingestion ·{" "}
                    {[trace.scenario, trace.mode, trace.stage].filter(Boolean).join(" · ") ||
                      "no metadata"}
                  </div>
                )}

                {trace.guardrails.length > 0 ? (
                  <div className="guardrail-flags">
                    {trace.guardrails.map((guardrail) => (
                      <div key={guardrail} className="guardrail-flag">
                        <span className="gf-name">{guardrail}</span>
                        <span className="gf-rest">→ guardrail triggered</span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })}

          {toolSummary.length > 0 ? (
            <div className="tools-used">
              <div className="tools-used-head">
                <span>Jaguar tools used</span>
                <b>{toolSummary.length}</b>
              </div>
              <div className="tools-used-grid">
                {toolSummary.slice(0, 12).map((tool) => (
                  <div key={`${tool.server ?? "unknown"}-${tool.name}`} className="tool-chip">
                    <span>{tool.name}</span>
                    <b>{tool.server ?? "mcp"}</b>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function summarizeTools(traces: TraceView[]): { name: string; server: string | null }[] {
  const byName = new Map<string, { name: string; server: string | null }>();

  for (const trace of traces) {
    for (const tool of trace.tools) {
      const rawName = tool.tool ?? inferToolFromSpan(tool.spanName);
      if (!rawName) continue;
      const name = rawName.replace(/_(?:jaguawm|(?=[a-z0-9]*\d)[a-z0-9]{6,8})$/i, "");
      const existing = byName.get(name);
      if (!existing || (!existing.server && tool.server)) {
        byName.set(name, { name, server: tool.server });
      }
    }
  }

  return [...byName.values()].sort((a, b) => a.name.localeCompare(b.name));
}

function inferToolFromSpan(spanName: string | null): string | null {
  if (!spanName) return null;
  const match =
    spanName.match(/tools\/call:\s*([a-z][a-z0-9_]+)/i) ??
    spanName.match(/^(get_[\w]+|prepare_[\w]+|draft_[\w]+|search_[\w]+)/i);
  return match?.[1]?.replace(/_jaguawm$/i, "") ?? null;
}
