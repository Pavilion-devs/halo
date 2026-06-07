export type IncidentMode = "normal" | "degraded" | "blackout";

export type IncidentEvent = {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type Approval = {
  id: string;
  action_type: string;
  status: "pending" | "approved" | "rejected";
  external_system: string | null;
  external_action_id: string | null;
  external_status: string | null;
  risk: string | null;
  title: string | null;
  details: Record<string, unknown>;
  requested_at: string;
  resolved_at: string | null;
};

export type TraceLink = {
  incident_id: string;
  trace_id: string;
  metadata: Record<string, unknown>;
};

export type Checkpoint = {
  id: string;
  stage: string;
  state: Record<string, unknown>;
  created_at: string;
};

export type TraceSummary = {
  internal_id: string;
  trace_id: string;
  created_at: string;
  metadata: Record<string, unknown>;
  provisional: boolean;
  lookup_status: string;
  live_summary: Record<string, unknown> | null;
  error: string | null;
};

export type Incident = {
  id: string;
  title: string;
  severity: "sev1" | "sev2" | "sev3";
  status: string;
  environment: string;
  product: string;
  mode: IncidentMode;
  stage: string;
  summary: string | null;
  latest_recommendation: string | null;
  current_agent: string;
  current_virtual_model: string;
  last_failure: string | null;
  fallback_action: string | null;
  checkpoint_index: number;
  created_at: string;
  updated_at: string;
  events: IncidentEvent[];
  checkpoints: Checkpoint[];
  approvals: Approval[];
  trace_links: TraceLink[];
};

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type IncidentListResult = {
  incidents: Incident[];
  error: string | null;
  usingDemoData: boolean;
};

export type IncidentDetailResult = {
  incident: Incident | null;
  error: string | null;
  usingDemoData: boolean;
};

export async function getIncidents(): Promise<IncidentListResult> {
  try {
    const response = await fetch(`${apiBaseUrl}/incidents`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return incidentsFallback(`API returned ${response.status} while loading incidents.`);
    }
    const payload = (await response.json()) as { incidents: Incident[] };
    return {
      incidents: payload.incidents,
      error: null,
      usingDemoData: false
    };
  } catch {
    return incidentsFallback("API is unreachable while loading incidents.");
  }
}

export async function getIncident(id: string): Promise<IncidentDetailResult> {
  try {
    const response = await fetch(`${apiBaseUrl}/incidents/${id}`, {
      cache: "no-store"
    });
    if (response.ok) {
      const payload = (await response.json()) as { incident: Incident };
      return {
        incident: payload.incident,
        error: null,
        usingDemoData: false
      };
    }
    return incidentFallback(id, `API returned ${response.status} while loading incident ${id}.`);
  } catch {
    return incidentFallback(id, `API is unreachable while loading incident ${id}.`);
  }
}

export type IncidentTracesResult = {
  traces: TraceSummary[];
  error: string | null;
};

export async function getIncidentTraces(id: string): Promise<IncidentTracesResult> {
  try {
    const response = await fetch(`${apiBaseUrl}/incidents/${id}/traces`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return { traces: [], error: `API returned ${response.status} while loading traces.` };
    }
    const payload = (await response.json()) as {
      traces: TraceSummary[];
      error: string | null;
    };
    return { traces: payload.traces ?? [], error: payload.error ?? null };
  } catch {
    return { traces: [], error: "API is unreachable while loading traces." };
  }
}

function incidentsFallback(error: string): IncidentListResult {
  return {
    incidents: [],
    error,
    usingDemoData: false
  };
}

function incidentFallback(_id: string, error: string): IncidentDetailResult {
  return {
    incident: null,
    error,
    usingDemoData: false
  };
}
