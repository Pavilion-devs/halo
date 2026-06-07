import { getIncidents, type Incident, type IncidentEvent } from "./api";

export type ModeName = "normal" | "degraded" | "blackout";

const ACTIVE_STATUSES = new Set(["open", "running", "waiting_for_approval"]);
const RESOLVED_STATUSES = new Set(["closed", "handed_off"]);
const MODE_SEVERITY: Record<ModeName, number> = { normal: 0, degraded: 1, blackout: 2 };
const SEVERITY_RANK: Record<string, number> = { sev1: 3, sev2: 2, sev3: 1 };
const WEEKDAY = ["S", "M", "T", "W", "T", "F", "S"];

export type DayBucket = {
  day: string;
  height: number;
  count: number;
  tone: "flat" | "on" | "peak";
  peakLabel: string | null;
};

export type RecentEvent = {
  id: string;
  type: string;
  mode: ModeName | null;
  incidentId: string;
  incidentTitle: string;
  createdAt: string;
};

export type DashboardModel = {
  incidents: Incident[];
  activeIncidents: Incident[];
  systemMode: ModeName;
  stats: {
    activeIncidents: number;
    resolved: number;
    failuresAbsorbed: number;
    checkpoints: number;
    pendingApprovals: number;
  };
  buckets: DayBucket[];
  totalEvents: number;
  continuity: { percent: number; normal: number; degraded: number; blackout: number };
  spotlight: Incident | null;
  recentEvents: RecentEvent[];
  uptimeStartedAt: string | null;
  lastHeartbeatAt: string | null;
  usingDemoData: boolean;
  error: string | null;
};

const payloadMode = (event: IncidentEvent): ModeName | null => {
  const value = event.payload?.mode;
  return value === "normal" || value === "degraded" || value === "blackout" ? value : null;
};

const isDowngrade = (event: IncidentEvent): boolean =>
  event.type === "mode.changed" &&
  (payloadMode(event) === "degraded" || payloadMode(event) === "blackout");

const dayKey = (iso: string): string => new Date(iso).toISOString().slice(0, 10);

function buildBuckets(events: IncidentEvent[]): { buckets: DayBucket[]; total: number } {
  const counts = new Map<string, number>();
  for (const event of events) {
    const key = dayKey(event.created_at);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const today = new Date();
  const days: { key: string; label: string; count: number }[] = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const date = new Date(today);
    date.setDate(today.getDate() - offset);
    const key = date.toISOString().slice(0, 10);
    days.push({ key, label: WEEKDAY[date.getDay()], count: counts.get(key) ?? 0 });
  }

  const max = Math.max(0, ...days.map((d) => d.count));
  const peakIndex = max > 0 ? days.findIndex((d) => d.count === max) : -1;

  const buckets = days.map((d, index) => ({
    day: d.label,
    count: d.count,
    height: max > 0 ? Math.max(8, Math.round((d.count / max) * 100)) : 8,
    tone: (d.count === 0 ? "flat" : index === peakIndex ? "peak" : "on") as DayBucket["tone"],
    peakLabel: index === peakIndex && max > 0 ? String(d.count) : null
  }));

  return { buckets, total: days.reduce((sum, d) => sum + d.count, 0) };
}

export async function getDashboardModel(): Promise<DashboardModel> {
  const { incidents, error, usingDemoData } = await getIncidents();

  const activeIncidents = incidents.filter((i) => ACTIVE_STATUSES.has(i.status));
  const resolved = incidents.filter((i) => RESOLVED_STATUSES.has(i.status)).length;

  const allEvents = incidents.flatMap((incident) =>
    incident.events.map((event) => ({ event, incident }))
  );

  const failuresAbsorbed = allEvents.filter(
    ({ event }) => event.type === "truefoundry.invocation_failed" || isDowngrade(event)
  ).length;

  const checkpoints = incidents.reduce((sum, i) => sum + (i.checkpoint_index ?? 0), 0);
  const pendingApprovals = incidents.reduce(
    (sum, i) => sum + i.approvals.filter((a) => a.status === "pending").length,
    0
  );

  const systemMode = activeIncidents.reduce<ModeName>(
    (worst, i) => (MODE_SEVERITY[i.mode] > MODE_SEVERITY[worst] ? i.mode : worst),
    "normal"
  );

  const modeCounts = incidents.reduce(
    (acc, i) => {
      acc[i.mode] += 1;
      return acc;
    },
    { normal: 0, degraded: 0, blackout: 0 }
  );
  const continuityPercent =
    incidents.length > 0
      ? Math.round(((incidents.length - modeCounts.blackout) / incidents.length) * 100)
      : 100;

  const spotlight =
    [...activeIncidents].sort((a, b) => {
      const sev = (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0);
      if (sev !== 0) return sev;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    })[0] ?? null;

  const recentEvents: RecentEvent[] = allEvents
    .map(({ event, incident }) => ({
      id: event.id,
      type: event.type,
      mode: payloadMode(event) ?? incident.mode,
      incidentId: incident.id,
      incidentTitle: incident.title,
      createdAt: event.created_at
    }))
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 6);

  const createdTimes = incidents.map((i) => new Date(i.created_at).getTime());
  const eventTimes = allEvents.map(({ event }) => new Date(event.created_at).getTime());
  const updatedTimes = incidents.map((i) => new Date(i.updated_at).getTime());
  const uptimeStartedAt = createdTimes.length
    ? new Date(Math.min(...createdTimes)).toISOString()
    : null;
  const heartbeatPool = [...eventTimes, ...updatedTimes];
  const lastHeartbeatAt = heartbeatPool.length
    ? new Date(Math.max(...heartbeatPool)).toISOString()
    : null;

  const { buckets, total } = buildBuckets(allEvents.map(({ event }) => event));

  return {
    incidents,
    activeIncidents,
    systemMode,
    stats: {
      activeIncidents: activeIncidents.length,
      resolved,
      failuresAbsorbed,
      checkpoints,
      pendingApprovals
    },
    buckets,
    totalEvents: total,
    continuity: { percent: continuityPercent, ...modeCounts },
    spotlight,
    recentEvents,
    uptimeStartedAt,
    lastHeartbeatAt,
    usingDemoData,
    error
  };
}

const toMs = (iso: string): number => {
  // SQLite-stored timestamps come back without a timezone; treat them as UTC
  // so a UTC+offset viewer doesn't see everything shifted into the past.
  const hasTz = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasTz ? iso : `${iso}Z`).getTime();
};

export const relativeTime = (iso: string): string => {
  const ms = Date.now() - toMs(iso);
  if (ms < 45_000) return "just now";
  const mins = Math.round(ms / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return rem === 0 ? `${hrs}h ago` : `${hrs}h ${rem}m ago`;
};

export const prettyEventType = (type: string): string =>
  type
    .replace(/[._]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

export const prettyStage = (stage: string): string =>
  stage.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
