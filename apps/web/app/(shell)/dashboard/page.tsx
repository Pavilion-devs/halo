import { ActiveIncidentCard } from "@/components/dashboard/active-incident-card";
import { ContinuityGauge } from "@/components/dashboard/continuity-gauge";
import { EventsWeekChart } from "@/components/dashboard/events-week-chart";
import { HaloUptime } from "@/components/dashboard/halo-uptime";
import { IncidentsCard } from "@/components/dashboard/incidents-card";
import { ModePosture } from "@/components/dashboard/mode-posture";
import { RecentEventsCard } from "@/components/dashboard/recent-events-card";
import { StatCard } from "@/components/dashboard/stat-card";
import { getDashboardModel } from "@/lib/dashboard";

export const dynamic = "force-dynamic";

const TrendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Trend</title>
    <path
      d="M6 16V8M6 8l-3 3M6 8l3 3M14 5l6 6M14 5v14"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

const ShieldIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Recovered</title>
    <path
      d="M12 3 5 6v6c0 4 3 6.5 7 9 4-2.5 7-5 7-9V6l-7-3Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SaveIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Checkpoint</title>
    <path
      d="M5 4h11l3 3v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path d="M8 4v5h7V4M8 20v-6h8v6" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
  </svg>
);

const GateIcon = () => (
  <svg viewBox="0 0 24 24" fill="none">
    <title>Approval</title>
    <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" strokeWidth="1.8" />
    <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export default async function DashboardPage() {
  const model = await getDashboardModel();
  const { stats, continuity } = model;

  return (
    <>
      <div className="page-head with-actions">
        <div>
          <h1>Dashboard</h1>
          <div className="sub">
            Live resilience view across every incident Halo is commanding.{" "}
            {model.usingDemoData ? "Showing demo fixture data." : "Connected to the live Halo API."}
          </div>
          {model.error && model.incidents.length === 0 ? (
            <div className="demo-banner" style={{ marginTop: 12 }}>
              {model.error}
            </div>
          ) : null}
        </div>
        <ModePosture systemMode={model.systemMode} />
      </div>

      <div className="dash-grid">
        <StatCard
          variant="stat-1"
          dark
          title="Active Incidents"
          value={String(stats.activeIncidents)}
          footIcon={<TrendIcon />}
          footText={`${stats.resolved} resolved / handed off`}
        />
        <StatCard
          variant="stat-2"
          title="Failures Absorbed"
          value={String(stats.failuresAbsorbed)}
          footIcon={<ShieldIcon />}
          footText="Caught & recovered, no crash"
        />
        <StatCard
          variant="stat-3"
          title="Checkpoints"
          value={String(stats.checkpoints)}
          footIcon={<SaveIcon />}
          footText="State preserved across steps"
        />
        <StatCard
          variant="stat-4"
          title="Pending Approvals"
          value={String(stats.pendingApprovals)}
          footIcon={<GateIcon />}
          footText={
            stats.pendingApprovals > 0 ? "Awaiting human sign-off" : "No unsafe action waiting"
          }
        />

        <EventsWeekChart buckets={model.buckets} total={model.totalEvents} />
        <ActiveIncidentCard incident={model.spotlight} />
        <IncidentsCard incidents={model.activeIncidents} />
        <RecentEventsCard events={model.recentEvents} />
        <ContinuityGauge
          percent={continuity.percent}
          normal={continuity.normal}
          degraded={continuity.degraded}
          blackout={continuity.blackout}
        />
        <HaloUptime startedAt={model.uptimeStartedAt} heartbeatAt={model.lastHeartbeatAt} />
      </div>
    </>
  );
}
