import type { DayBucket } from "@/lib/dashboard";

type Props = {
  buckets: DayBucket[];
  total: number;
};

const Dots = () => (
  <svg width={18} height={18} viewBox="0 0 24 24" fill="none">
    <title>More</title>
    <circle cx="5" cy="12" r="1.6" fill="currentColor" />
    <circle cx="12" cy="12" r="1.6" fill="currentColor" />
    <circle cx="19" cy="12" r="1.6" fill="currentColor" />
  </svg>
);

export function EventsWeekChart({ buckets, total }: Props) {
  return (
    <div className="card c-analytics">
      <div className="analytics-head">
        <h3>Workflow Events · last 7 days</h3>
        <div className="menu" aria-label="More">
          <Dots />
        </div>
      </div>
      <div className="chart">
        {buckets.map((bucket, idx) => {
          const barClass =
            bucket.tone === "peak" ? "bar peak" : bucket.tone === "on" ? "bar on" : "bar";
          return (
            <div key={`${bucket.day}-${idx}`} className="bar-wrap">
              <div className={barClass} style={{ height: `${bucket.height}%` }}>
                {bucket.peakLabel ? <div className="peak-label">{bucket.peakLabel}</div> : null}
              </div>
              <div className="bar-label">{bucket.day}</div>
            </div>
          );
        })}
      </div>
      <div
        style={{
          padding: "0 22px 18px",
          fontSize: 12,
          color: "var(--ink-dim)",
          letterSpacing: "-0.01em"
        }}
      >
        {total} total {total === 1 ? "event" : "events"} this week
      </div>
    </div>
  );
}
