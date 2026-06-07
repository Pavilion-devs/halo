"use server";

import { revalidatePath } from "next/cache";

import { apiBaseUrl } from "@/lib/api";
import { WAR_ROOM_SCENARIO } from "@/lib/war-room";

export type ActionResult = { ok: boolean; message: string };

const jsonHeaders = { "Content-Type": "application/json" };

export async function runNextStep(
  incidentId: string,
  forceMode?: string
): Promise<ActionResult> {
  const body: Record<string, unknown> = { scenario: WAR_ROOM_SCENARIO, demo_run: true };
  if (forceMode) body.force_mode = forceMode;
  try {
    const response = await fetch(`${apiBaseUrl}/incidents/${incidentId}/run`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
      cache: "no-store"
    });
    if (!response.ok) {
      return { ok: false, message: `Run failed (HTTP ${response.status}).` };
    }
    revalidatePath(`/incidents/${incidentId}`);
    return { ok: true, message: "Workflow advanced one step." };
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Run failed." };
  }
}

export async function resolveApproval(
  incidentId: string,
  approvalId: string,
  approved: boolean,
  note?: string
): Promise<ActionResult> {
  try {
    const response = await fetch(`${apiBaseUrl}/incidents/${incidentId}/approve`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ approval_id: approvalId, approved, note: note || null }),
      cache: "no-store"
    });
    if (!response.ok) {
      return { ok: false, message: `Approval failed (HTTP ${response.status}).` };
    }
    revalidatePath(`/incidents/${incidentId}`);
    return { ok: true, message: approved ? "Action approved." : "Action rejected — handoff prepared." };
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Approval failed." };
  }
}

const CHAOS_PATHS: Record<string, string> = {
  fail: "/demo/fail-next",
  delay: "/demo/delay-next?delay_ms=1500",
  bad: "/demo/return-bad-payload"
};

export async function armChaos(
  incidentId: string,
  effect: "fail" | "delay" | "bad"
): Promise<ActionResult> {
  const path = CHAOS_PATHS[effect];
  const separator = path.includes("?") ? "&" : "?";
  const query = `incident_id=${encodeURIComponent(incidentId)}&scenario=${WAR_ROOM_SCENARIO}`;
  const labels: Record<string, string> = {
    fail: "Next tool call armed to fail.",
    delay: "Next tool call armed to time out.",
    bad: "Next tool call armed to return a malformed payload."
  };
  try {
    const response = await fetch(`${apiBaseUrl}${path}${separator}${query}`, {
      method: "POST",
      cache: "no-store"
    });
    if (!response.ok) {
      return { ok: false, message: `Could not arm chaos (HTTP ${response.status}).` };
    }
    return { ok: true, message: `${labels[effect]} Run the next step to trigger it.` };
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Could not arm chaos." };
  }
}
