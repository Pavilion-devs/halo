type Props = {
  percent: number;
  normal: number;
  degraded: number;
  blackout: number;
};

const GAUGE_ARC = "M 30 124 A 90 90 0 0 1 210 124";

export function ContinuityGauge({ percent, normal, degraded, blackout }: Props) {
  const clamped = Math.max(0, Math.min(100, percent));
  const display = Math.round(clamped);

  return (
    <div className="card c-progress">
      <div className="gauge-head">
        <h3>Continuity</h3>
        <div className="menu">
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none">
            <title>More</title>
            <circle cx="5" cy="12" r="1.5" fill="currentColor" />
            <circle cx="12" cy="12" r="1.5" fill="currentColor" />
            <circle cx="19" cy="12" r="1.5" fill="currentColor" />
          </svg>
        </div>
      </div>
      <div className="gauge-wrap">
        <svg
          className="gauge-svg"
          viewBox="0 0 240 160"
          role="img"
          aria-label={`Continuity ${display}%`}
        >
          <title>Continuity gauge</title>
          <defs>
            <pattern
              id="gaugeStripe"
              patternUnits="userSpaceOnUse"
              width={6}
              height={6}
              patternTransform="rotate(45)"
            >
              <rect width={6} height={6} fill="#eef0ea" />
              <rect width={3} height={6} fill="#e3e5df" />
            </pattern>
          </defs>
          <path
            d={GAUGE_ARC}
            fill="none"
            style={{ stroke: "var(--gauge-track, url(#gaugeStripe))" }}
            strokeWidth={26}
            strokeLinecap="round"
            pathLength={100}
          />
          {clamped > 0 ? (
            <>
              <path
                d={GAUGE_ARC}
                fill="none"
                style={{ stroke: "var(--gauge-arc, #14593a)" }}
                strokeWidth={26}
                strokeLinecap="round"
                pathLength={100}
                strokeDasharray={`${clamped} ${100 - clamped}`}
              />
              <path
                d={GAUGE_ARC}
                fill="none"
                style={{ stroke: "var(--gauge-arc-2, #2ea86b)" }}
                strokeWidth={16}
                strokeLinecap="round"
                pathLength={100}
                strokeDasharray={`${clamped} ${100 - clamped}`}
              />
            </>
          ) : null}
        </svg>
        <div className="gauge-value">
          <div className="pct">{display}%</div>
          <div className="lbl">Stayed operational</div>
        </div>
      </div>
      <div className="gauge-legend">
        <div className="lg">
          <span className="sw c" />
          Normal · {normal}
        </div>
        <div className="lg">
          <span className="sw p" />
          Degraded · {degraded}
        </div>
        <div className="lg">
          <span className="sw pd" />
          Blackout · {blackout}
        </div>
      </div>
    </div>
  );
}
