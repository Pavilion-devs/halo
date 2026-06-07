import type { IncidentEvent, TraceLink, TraceSummary } from "./api";

export const STAGE_SEQUENCE = [
  "intake",
  "classify",
  "gather_evidence",
  "draft_plan",
  "execute_safe_actions",
  "request_approval",
  "monitor",
  "handoff_or_close"
] as const;

export const STAGE_TOTAL = STAGE_SEQUENCE.length;

export const stageIndex = (stage: string): number => {
  const index = STAGE_SEQUENCE.indexOf(stage as (typeof STAGE_SEQUENCE)[number]);
  return index < 0 ? 0 : index + 1;
};

export type EventTone = "ok" | "warn" | "bad" | "info";

export const eventTone = (event: IncidentEvent): EventTone => {
  const mode = event.payload?.mode;
  switch (event.type) {
    case "truefoundry.invocation_failed":
    case "approval.not_found":
      return "bad";
    case "approval.requested":
      return "warn";
    case "external.action_executed":
      return "ok";
    case "verification.completed":
      return event.payload?.outcome === "recovered" ? "ok" : "warn";
    case "mode.changed":
      return mode === "normal" ? "ok" : "warn";
    case "approval.resolved":
      return event.payload?.approved === false ? "bad" : "ok";
    case "workflow.stage_completed":
    case "truefoundry.invocation_succeeded":
      return "ok";
    default:
      return "info";
  }
};

export const TONE_PILL: Record<EventTone, string> = {
  ok: "verdict-pill enter",
  warn: "verdict-pill watch",
  bad: "verdict-pill ignore",
  info: "tone-pill info"
};

export const eventSummary = (event: IncidentEvent): string => {
  const p = event.payload ?? {};
  const parts: string[] = [];
  const push = (key: string, prefix = "") => {
    const value = p[key];
    if (typeof value === "string" && value) parts.push(`${prefix}${value}`);
  };
  push("reason");
  push("error");
  push("action_type");
  push("external_action_id", "request ");
  push("outcome");
  push("result");
  push("mode", "mode ");
  push("agent");
  if (typeof p.trace_id === "string") parts.push(`trace ${p.trace_id.slice(0, 10)}…`);
  if (parts.length === 0 && typeof p.stage === "string") parts.push(`stage ${p.stage}`);
  return parts.join(" · ") || "—";
};

export type TraceView = {
  traceId: string;
  status: string | null;
  modelName: string | null;
  spanCount: number | null;
  rootSpanName: string | null;
  guardrails: string[];
  tools: ToolSpanView[];
  provisional: boolean;
  lookupStatus: string;
  scenario: string | null;
  mode: string | null;
  stage: string | null;
  failure: boolean;
};

export type ToolSpanView = {
  server: string | null;
  tool: string | null;
  status: string | null;
  spanName: string | null;
};

const metaString = (meta: Record<string, unknown>, key: string): string | null =>
  typeof meta[key] === "string" ? (meta[key] as string) : null;

export const toTraceView = (trace: TraceSummary): TraceView => {
  const ls = trace.live_summary ?? {};
  const meta = trace.metadata ?? {};
  const guardrails = Array.isArray(ls.guardrails_triggered)
    ? (ls.guardrails_triggered as unknown[]).map(String)
    : [];
  const tools = Array.isArray(ls.mcp_tool_spans)
    ? (ls.mcp_tool_spans as unknown[])
        .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
        .map((item) => ({
          server: typeof item.server === "string" ? item.server : null,
          tool: typeof item.tool === "string" ? item.tool : null,
          status: typeof item.status === "string" ? item.status : null,
          spanName: typeof item.span_name === "string" ? item.span_name : null
        }))
    : [];
  return {
    traceId: trace.trace_id,
    status: typeof ls.status === "string" ? ls.status : null,
    modelName: typeof ls.model_name === "string" ? ls.model_name : null,
    spanCount: typeof ls.span_count === "number" ? ls.span_count : null,
    rootSpanName: typeof ls.root_span_name === "string" ? ls.root_span_name : null,
    guardrails,
    tools,
    provisional: trace.provisional,
    lookupStatus: trace.lookup_status,
    scenario: metaString(meta, "scenario"),
    mode: metaString(meta, "mode"),
    stage: metaString(meta, "stage"),
    failure: meta.failure === true || meta.failure === "true"
  };
};

export const traceViewFromLink = (link: TraceLink): TraceView => {
  const meta = link.metadata ?? {};
  return {
    traceId: link.trace_id,
    status: null,
    modelName: metaString(meta, "model") ?? null,
    spanCount: null,
    rootSpanName: null,
    guardrails: [],
    tools: [],
    provisional: link.trace_id.startsWith("pending-"),
    lookupStatus: "pending",
    scenario: metaString(meta, "scenario"),
    mode: metaString(meta, "mode"),
    stage: metaString(meta, "stage"),
    failure: meta.failure === true || meta.failure === "true"
  };
};

export const shortModel = (model: string | null): string => {
  if (!model) return "—";
  const match = model.match(/claude[\w.-]*/i);
  if (!match) return model;
  const short = match[0].replace(/-v\d+$/, "");
  const provider = model.includes("/") ? model.split("/")[0] : null;
  return provider ? `${provider} · ${short}` : short;
};

export const WAR_ROOM_SCENARIO = "war-room";

export type ReadSection = {
  label: string;
  body: string;
};

export type PreparedAction = {
  id: string;
  name: string;
  risk: string | null;
  status: string | null;
};

export type ParsedRecommendation = {
  headline: string;
  sections: ReadSection[];
  preparedActions: PreparedAction[];
};

const SECTION_MARKERS = [
  { label: "Classification", markers: ["classification"] },
  { label: "Root cause", markers: ["root cause"] },
  { label: "Impact", markers: ["impact"] },
  { label: "Evidence", markers: ["evidence"] },
  { label: "Why not rollback", markers: ["why this is not a bad deploy", "why this is not a bad rollback"] },
  { label: "Recommended action", markers: ["recovery action prepared", "actions prepared", "recommended recovery", "recommended action"] },
  { label: "Action details", markers: ["what it will do"] },
  { label: "Verification plan", markers: ["verification after approval", "verification plan"] },
  { label: "Escalation path", markers: ["escalation path"] }
] as const;

export function parseRecommendation(raw: string | null | undefined): ParsedRecommendation {
  if (!raw) {
    return {
      headline: "Run the next workflow step to get Halo's recommendation.",
      sections: [],
      preparedActions: []
    };
  }

  const normalized = raw.replace(/\r/g, "").replace(/[📋🔄⏳]/g, "").replace(/\n{3,}/g, "\n\n");
  const preparedActions = extractPreparedActions(normalized);
  const semanticSections = extractSemanticSections(normalized, preparedActions);
  const sections = semanticSections.length > 0 ? semanticSections : extractSections(normalized);
  const headline =
    sections.find((section) => section.label === "Root cause")?.body ??
    stripMarkdown(normalized).split(/\n+/)[0] ??
    normalized;

  return {
    headline: compact(headline, 180),
    sections: sections.length > 0 ? sections : [{ label: "Recommendation", body: stripMarkdown(normalized) }],
    preparedActions
  };
}

function extractSemanticSections(text: string, actions: PreparedAction[]): ReadSection[] {
  const sections: ReadSection[] = [];
  const classification = text.match(/classification:\s*\*\*([^*]+)\*\*/i)?.[1];
  if (classification) sections.push({ label: "Classification", body: stripMarkdown(classification) });

  const tableRows = new Map<string, string>();
  const rowPattern = /^\|\s*\*\*([^*]+)\*\*\s*\|\s*(.*?)\s*\|\s*$/gim;
  for (const match of text.matchAll(rowPattern)) {
    tableRows.set(match[1].toLowerCase(), stripMarkdown(match[2]));
  }

  const rowLabels: [string, string][] = [
    ["status", "Status"],
    ["impact", "Impact"],
    ["root cause", "Root cause"],
    ["evidence", "Evidence"]
  ];
  for (const [key, label] of rowLabels) {
    const body = tableRows.get(key);
    if (body) sections.push({ label, body });
  }

  if (actions.length > 0) {
    sections.push({
      label: "Recommended action",
      body: actions
        .map((action) =>
          [
            action.name,
            `request ${action.id}`,
            action.status ?? "Prepared",
            action.risk ? `risk ${action.risk}` : null
          ]
            .filter(Boolean)
            .join(" — ")
        )
        .join("\n")
    });
  }

  const actionDetails = text.match(/what it will do:\*\*\s*([\s\S]*?)(?=\n\n\*\*verification|\n\n###|\n\n---|$)/i)?.[1];
  if (actionDetails) sections.push({ label: "Action details", body: cleanSection(actionDetails) });

  const verification = text.match(/verification after approval:\*\*\s*([\s\S]*?)(?=\n\n###|\n\n---|$)/i)?.[1];
  if (verification) sections.push({ label: "Verification plan", body: cleanSection(verification) });

  const escalation = text.match(/escalation path[^\\n]*\n([\s\S]*?)(?=\n\n---|$)/i)?.[1];
  if (escalation) sections.push({ label: "Escalation path", body: cleanSection(escalation) });

  return sections.filter((section) => section.body.length > 0);
}

function extractSections(text: string): ReadSection[] {
  const lower = text.toLowerCase();
  const hits = SECTION_MARKERS.flatMap((section) => {
    const marker = section.markers
      .map((candidate) => ({ candidate, index: lower.indexOf(candidate) }))
      .filter((candidate) => candidate.index >= 0)
      .sort((a, b) => a.index - b.index)[0];
    return marker ? [{ label: section.label, marker: marker.candidate, index: marker.index }] : [];
  }).sort((a, b) => a.index - b.index);

  return hits
    .map((hit, index) => {
      const start = hit.index + hit.marker.length;
      const end = hits[index + 1]?.index ?? text.length;
      return {
        label: hit.label,
        body: cleanSection(text.slice(start, end))
      };
    })
    .filter((section) => section.body.length > 0);
}

function extractPreparedActions(text: string): PreparedAction[] {
  const actions: PreparedAction[] = [];
  const rowPattern = /\*\*([^*|]+)\*\*\s*\|\s*`?([a-z0-9_-]{12,})`?\s*\|\s*([^|\n]+)\|\s*([^|\n]+)/gi;
  for (const match of text.matchAll(rowPattern)) {
    actions.push({
      name: stripMarkdown(match[1]).trim(),
      id: match[2].trim(),
      status: stripMarkdown(match[3]).trim() || null,
      risk: stripMarkdown(match[4]).trim() || null
    });
  }

  if (actions.length > 0) return uniqueActions(actions);

  const id = text.match(/(?:action\s+id|request\s+id|id)\s*[:|]\s*`?([a-z0-9_-]{12,})`?/i)?.[1];
  if (!id) return [];
  const name =
    text.match(/\*\*([A-Za-z][^*|]{2,60})\*\*\s*\|\s*`?[a-z0-9_-]{12,}`?/i)?.[1] ??
    text.match(/prepared\s+(?:an?\s+)?([A-Za-z][A-Za-z\s-]{2,60})/i)?.[1] ??
    "Prepared action";
  return [
    {
      id,
      name: stripMarkdown(name).trim(),
      status: /awaiting operator approval/i.test(text) ? "Awaiting Operator Approval" : "Prepared",
      risk: text.match(/\|\s*(low|medium|high|critical)\s*(?:\||$)/i)?.[1] ?? null
    }
  ];
}

function uniqueActions(actions: PreparedAction[]): PreparedAction[] {
  const seen = new Set<string>();
  return actions.filter((action) => {
    if (seen.has(action.id)) return false;
    seen.add(action.id);
    return true;
  });
}

function cleanSection(value: string): string {
  return stripMarkdown(value)
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !/^-+\|?[-|\s]*$/.test(line) && !/^\|?\s*action\s*\|/i.test(line))
    .join("\n")
    .replace(/\s+\|\s+/g, " ")
    .replace(/\s+-\s+/g, "\n")
    .trim();
}

function stripMarkdown(value: string): string {
  return value
    .replace(/^[-\s#]+/gm, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/\|/g, " | ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function compact(value: string, limit: number): string {
  const clean = value.replace(/\s+/g, " ").trim();
  return clean.length > limit ? `${clean.slice(0, limit - 1).trim()}…` : clean;
}
