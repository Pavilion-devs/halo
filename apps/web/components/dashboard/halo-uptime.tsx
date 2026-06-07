"use client";

import { useEffect, useState } from "react";

type Props = {
  startedAt: string | null;
  heartbeatAt: string | null;
};

const formatDuration = (ms: number) => {
  if (ms <= 0) return "00:00:00";
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
};

export function HaloUptime({ startedAt, heartbeatAt }: Props) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const startedMs = startedAt ? new Date(startedAt).getTime() : null;
  const heartbeatMs = heartbeatAt ? new Date(heartbeatAt).getTime() : null;
  const uptime = startedMs ? formatDuration(now - startedMs) : "--:--:--";
  const heartbeatAgeSec = heartbeatMs ? Math.round((now - heartbeatMs) / 1000) : null;

  const healthLabel =
    heartbeatAgeSec === null
      ? "No pulse yet"
      : heartbeatAgeSec <= 90
        ? `Live · ${heartbeatAgeSec}s ago`
        : heartbeatAgeSec <= 600
          ? `Idle · ${Math.round(heartbeatAgeSec / 60)}m ago`
          : `Quiet · ${Math.round(heartbeatAgeSec / 60)}m ago`;

  const healthTone =
    heartbeatAgeSec === null
      ? "rgba(240, 140, 150, 0.85)"
      : heartbeatAgeSec <= 90
        ? "rgba(130, 230, 170, 0.95)"
        : "rgba(255, 195, 120, 0.9)";

  return (
    <div className="card dark tracker c-tracker">
      <h3>Halo Uptime</h3>
      <div className="time">{uptime}</div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12.5,
          color: healthTone,
          marginTop: 4
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "currentColor",
            boxShadow: "0 0 6px currentColor"
          }}
        />
        {healthLabel}
      </div>
    </div>
  );
}
