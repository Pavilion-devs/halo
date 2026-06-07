import { ChevronLeft } from "lucide-react";
import Link from "next/link";

import { ModePosture } from "@/components/dashboard/mode-posture";
import { StatCard } from "@/components/dashboard/stat-card";
import { ApprovalGate } from "@/components/war-room/approval-gate";
import { HaloReadCard } from "@/components/war-room/halo-read-card";
import { IncidentTimeline } from "@/components/war-room/incident-timeline";
import { ModeHero } from "@/components/war-room/mode-hero";
import { TraceEvidence } from "@/components/war-room/trace-evidence";
import { getIncident, getIncidentTraces } from "@/lib/api";
import { prettyStage, relativeTime } from "@/lib/dashboard";
import {
  STAGE_TOTAL,
  parseRecommendation,
  stageIndex,
  toTraceView,
  traceViewFromLink
} from "@/lib/war-room";

export const dynamic = "force-dynamic";

const SEV_TONE: Record<string, string> = { sev1: "sev-1", sev2: "sev-2", sev3: "sev-3" };

const StageIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Stage</title>
    <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SaveIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Checkpoint</title>
    <path d="M5 4h11l3 3v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M8 4v5h7V4M8 20v-6h8v6" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
  </svg>
);

const ShieldIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Recovered</title>
    <path d="M12 3 5 6v6c0 4 3 6.5 7 9 4-2.5 7-5 7-9V6l-7-3Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default async function WarRoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [{ incident, error }, tracesResult] = await Promise.all([
    getIncident(id),
    getIncidentTraces(id)
  ]);

  if (!incident) {
    return (
      <div className="page-head">
        <div>
          <Link href="/incidents" className="wr-back">
            <ChevronLeft size={15} strokeWidth={2.5} aria-hidden />
            <span>Incidents</span>
          </Link>
          <h1>Incident unavailable</h1>
          <div className="sub">{error ?? "This incident could not be loaded."}</div>
        </div>
      </div>
    );
  }

  const failures = incident.events.filter(
    (event) =>
      event.type === "truefoundry.invocation_failed" ||
      (event.type === "mode.changed" && event.payload?.mode !== "normal")
  ).length;

  const traceViews =
    tracesResult.traces.length > 0
      ? tracesResult.traces.map(toTraceView)
      : incident.trace_links.map(traceViewFromLink);
  const parsedRecommendation = parseRecommendation(incident.latest_recommendation);

  return (
    <>
      <div className="page-head with-actions">
        <div>
          <Link href="/incidents" className="wr-back">
            <ChevronLeft size={15} strokeWidth={2.5} aria-hidden />
            <span>Incidents</span>
          </Link>
          <h1 style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            {incident.title}
            <span className={`sev-pill ${SEV_TONE[incident.severity] ?? "sev-2"}`}>
              {incident.severity.toUpperCase()}
            </span>
          </h1>
          <div className="sub">
            {incident.product} / {incident.environment} · {prettyStage(incident.stage)} ·{" "}
            {incident.status.replace(/_/g, " ")} · updated {relativeTime(incident.updated_at)}
          </div>
        </div>
        <ModePosture systemMode={incident.mode} />
      </div>

      <div className="dash-grid">
        <ModeHero mode={incident.mode} agent={incident.current_agent} />
        <StatCard
          variant="stat-2"
          title="Stage"
          value={`${stageIndex(incident.stage)} / ${STAGE_TOTAL}`}
          footIcon={<StageIcon />}
          footText={prettyStage(incident.stage)}
        />
        <StatCard
          variant="stat-3"
          title="Checkpoints"
          value={String(incident.checkpoint_index)}
          footIcon={<SaveIcon />}
          footText="State preserved"
        />
        <StatCard
          variant="stat-4"
          title="Failures Caught"
          value={String(failures)}
          footIcon={<ShieldIcon />}
          footText="Recovered via fallback"
        />
      </div>

      <div className="wr-body">
        <div className="wr-main">
          <HaloReadCard incident={incident} />
          <TraceEvidence traces={traceViews} />
        </div>
        <aside className="wr-rail">
          <ApprovalGate
            incidentId={incident.id}
            approvals={incident.approvals}
            preparedActions={parsedRecommendation.preparedActions}
          />
        </aside>
      </div>

      <div className="dash-grid">
        <IncidentTimeline events={incident.events} />
      </div>
    </>
  );
}
