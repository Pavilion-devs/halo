"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { armChaos, runNextStep, type ActionResult } from "@/app/(shell)/incidents/[id]/actions";

type Props = {
  incidentId: string;
};

export function OperatorConsole({ incidentId }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [forceMode, setForceMode] = useState("");
  const [status, setStatus] = useState<ActionResult | null>(null);

  const run = () =>
    startTransition(async () => {
      setStatus(await runNextStep(incidentId, forceMode || undefined));
      router.refresh();
    });

  const chaos = (effect: "fail" | "delay" | "bad") =>
    startTransition(async () => {
      setStatus(await armChaos(incidentId, effect));
      router.refresh();
    });

  return (
    <div className="card c-discovery">
      <div className="list-head">
        <h3>Operator console</h3>
      </div>
      <div className="opc">
        <button className="btn primary opc-run" type="button" disabled={isPending} onClick={run}>
          {isPending ? "Working…" : "▸ Run next step"}
        </button>

        <label className="opc-field">
          <span className="opc-label">Force mode</span>
          <select
            className="opc-select"
            value={forceMode}
            onChange={(event) => setForceMode(event.target.value)}
            disabled={isPending}
          >
            <option value="">auto (let Halo decide)</option>
            <option value="normal">normal</option>
            <option value="degraded">degraded</option>
            <option value="blackout">blackout</option>
          </select>
        </label>

        <div className="opc-divider">
          <span>Inject failure (chaos)</span>
        </div>
        <div className="opc-chaos">
          <button className="btn danger" type="button" disabled={isPending} onClick={() => chaos("fail")}>
            Fail next tool
          </button>
          <button className="btn danger" type="button" disabled={isPending} onClick={() => chaos("delay")}>
            Delay next tool
          </button>
          <button className="btn danger" type="button" disabled={isPending} onClick={() => chaos("bad")}>
            Bad payload
          </button>
        </div>

        {status ? (
          <div className={`opc-status ${status.ok ? "ok" : "err"}`}>{status.message}</div>
        ) : (
          <div className="opc-hint">Arm a failure, then run the next step to watch Halo recover.</div>
        )}
      </div>
    </div>
  );
}
