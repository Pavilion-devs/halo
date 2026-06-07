"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { resolveApproval, type ActionResult } from "@/app/(shell)/incidents/[id]/actions";
import type { Approval } from "@/lib/api";
import type { PreparedAction } from "@/lib/war-room";

type Props = {
  incidentId: string;
  approvals: Approval[];
  preparedActions: PreparedAction[];
};

export function ApprovalGate({ incidentId, approvals, preparedActions }: Props) {
  const pending = approvals.find((approval) => approval.status === "pending") ?? null;
  const resolved = approvals.filter((approval) => approval.status !== "pending");
  const latestResolved = resolved.at(-1) ?? null;
  const externalPending = pending
    ? null
    : preparedActions.find(
        (action) => !approvals.some((approval) => approvalMatchesAction(approval, action))
      ) ?? null;

  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<ActionResult | null>(null);

  const decide = (approved: boolean) => {
    if (!pending) return;
    startTransition(async () => {
      setStatus(await resolveApproval(incidentId, pending.id, approved, note));
      router.refresh();
    });
  };

  return (
    <div className="card c-discovery">
      <div className="list-head">
        <h3>Approval gate</h3>
        <span
          className={`count-pill ${
            pending ? "" : externalPending ? "badge-external" : latestResolved ? "" : "muted"
          }`}
        >
          {pending
            ? "1 pending"
            : externalPending
              ? "external pending"
              : latestResolved
                ? latestResolved.external_status ?? latestResolved.status
                : "clear"}
        </span>
      </div>

      {pending ? (
        <div className="gate">
          <div className="gate-action">{pending.title ?? pending.action_type}</div>
          <div className="gate-sub">
            {pending.external_system === "jaguar"
              ? "Halo mirrored this Jaguar action request. Approval here calls Jaguar, then the VPS ops-runner executes it."
              : "Halo is holding this risky action for human sign-off."}
          </div>
          {pending.external_action_id ? (
            <div className="external-action-kv">
              <span>Action request</span>
              <b className="mono">{pending.external_action_id}</b>
            </div>
          ) : null}
          {pending.risk ? (
            <div className="external-action-kv">
              <span>Risk</span>
              <b>{pending.risk}</b>
            </div>
          ) : null}
          <textarea
            className="gate-note"
            placeholder="Optional note for the audit log…"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            disabled={isPending}
          />
          <div className="gate-actions">
            <button className="btn primary" type="button" disabled={isPending} onClick={() => decide(true)}>
              Approve
            </button>
            <button className="btn danger" type="button" disabled={isPending} onClick={() => decide(false)}>
              Reject
            </button>
          </div>
          {status ? (
            <div className={`opc-status ${status.ok ? "ok" : "err"}`}>{status.message}</div>
          ) : null}
        </div>
      ) : externalPending ? (
        <div className="gate external-gate">
          <div className="gate-action">{externalPending.name}</div>
          <div className="gate-sub">
            Jaguar prepared this action through MCP. If Halo has not mirrored it as a native approval yet,
            refresh after the latest workflow run or sync approvals before the demo.
          </div>
          <div className="external-action-kv">
            <span>Action request</span>
            <b className="mono">{externalPending.id}</b>
          </div>
          <div className="external-action-kv">
            <span>Status</span>
            <b>{externalPending.status ?? "Awaiting Operator Approval"}</b>
          </div>
          {externalPending.risk ? (
            <div className="external-action-kv">
              <span>Risk</span>
              <b>{externalPending.risk}</b>
            </div>
          ) : null}
          <div className="opc-status ok">
            Approval source: Jaguar ops. This card is read-only until Halo receives the synced approval.
          </div>
        </div>
      ) : latestResolved ? (
        <div className="gate-history">
          <div className="gate">
            <div className="gate-action">{latestResolved.title ?? latestResolved.action_type}</div>
            <div className="gate-sub">
              {latestResolved.external_system === "jaguar"
                ? latestResolved.status === "approved"
                  ? "Halo approved this Jaguar action and forwarded it to the live Jaguar ops path."
                  : "Halo rejected this Jaguar action and preserved the operator decision."
                : latestResolved.status === "approved"
                  ? "Halo approved this risky action and recorded the operator decision."
                  : "Halo rejected this risky action and preserved the handoff path."}
            </div>
            {latestResolved.external_action_id ? (
              <div className="external-action-kv">
                <span>Action request</span>
                <b className="mono">{latestResolved.external_action_id}</b>
              </div>
            ) : null}
            {latestResolved.external_status ? (
              <div className="external-action-kv">
                <span>External status</span>
                <b>{latestResolved.external_status}</b>
              </div>
            ) : null}
            {latestResolved.risk ? (
              <div className="external-action-kv">
                <span>Risk</span>
                <b>{latestResolved.risk}</b>
              </div>
            ) : null}
            {resolvedMessage(latestResolved) ? (
              <div className="opc-status ok">{resolvedMessage(latestResolved)}</div>
            ) : null}
          </div>

          {resolved.length > 1 ? (
            <div className="gate-history">
              {resolved
                .slice(0, -1)
                .reverse()
                .map((approval) => (
                  <div key={approval.id} className="gate-row">
                    <span className="gate-row-name">{approval.title ?? approval.action_type}</span>
                    <span
                      className={`verdict-pill ${
                        approval.status === "approved" ? "enter" : "ignore"
                      }`}
                    >
                      {approval.status}
                    </span>
                  </div>
                ))}
            </div>
          ) : null}

          {status ? (
            <div className={`opc-status ${status.ok ? "ok" : "err"}`}>{status.message}</div>
          ) : null}
        </div>
      ) : (
        <div className="empty-state">
          <strong>No gate pending</strong>
          No risky action is waiting on human approval right now.
        </div>
      )}
    </div>
  );
}

function approvalMatchesAction(approval: Approval, action: PreparedAction): boolean {
  if (approval.external_action_id && approval.external_action_id === action.id) {
    return true;
  }

  const approvalName = (approval.title ?? approval.action_type).trim().toLowerCase();
  const actionName = action.name.trim().toLowerCase();
  return approvalName.length > 0 && approvalName === actionName;
}

function resolvedMessage(approval: Approval): string | null {
  const externalResponse = approval.details?.external_response;
  if (typeof externalResponse === "string" && externalResponse) {
    return externalResponse;
  }
  if (approval.status === "approved") {
    return "Approval recorded. Halo can continue with the next safe step.";
  }
  if (approval.status === "rejected") {
    return "Rejection recorded. Halo should hand off instead of proceeding.";
  }
  return null;
}
