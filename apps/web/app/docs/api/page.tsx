import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "health", label: "Health" },
  { id: "create", label: "Create an incident" },
  { id: "list-get", label: "List & get" },
  { id: "run", label: "Run the next step" },
  { id: "approve", label: "Approve an action" },
  { id: "traces", label: "Trace evidence" }
];

export default function ApiReferencePage() {
  return (
    <DocPage
      eyebrow="Platform & deployment"
      title="API reference"
      description="The Halo incident API — create, list, run, approve, and inspect incidents. Served by the FastAPI workflow engine."
      toc={toc}
    >
      <Callout>
        In local development the API runs at <code>http://127.0.0.1:8000</code>. Interactive OpenAPI
        docs are at <code>/docs</code> (Swagger UI) and <code>/openapi.json</code>. All incident
        endpoints are under the <code>/incidents</code> prefix.
      </Callout>

      <h2 id="health">Health</h2>
      <p>
        <code>GET /health</code> and <code>GET /readiness</code> — liveness and readiness probes,
        return <code>200</code> when the service is up.
      </p>

      <h2 id="create">Create an incident</h2>
      <p><code>POST /incidents</code> → <code>201 Created</code></p>
      <pre>
        <code>{`{
  "title": "Jaguar worker offline after recent deploy",
  "severity": "sev1",
  "environment": "production",
  "product": "jaguar",
  "summary": "Worker heartbeat dropped after deploy; ingestion stalled."
}`}</code>
      </pre>
      <table>
        <thead>
          <tr><th>Field</th><th>Type</th><th>Notes</th></tr>
        </thead>
        <tbody>
          <tr><td><code>title</code></td><td>string</td><td>Required, 3–160 chars.</td></tr>
          <tr><td><code>severity</code></td><td>enum</td><td><code>sev1</code> | <code>sev2</code> | <code>sev3</code>. Defaults to <code>sev2</code>.</td></tr>
          <tr><td><code>environment</code></td><td>string</td><td>Defaults to the configured environment.</td></tr>
          <tr><td><code>product</code></td><td>string</td><td>Defaults to the configured product.</td></tr>
          <tr><td><code>summary</code></td><td>string | null</td><td>Optional.</td></tr>
        </tbody>
      </table>

      <h2 id="list-get">List &amp; get</h2>
      <p>
        <code>GET /incidents</code> returns <code>{`{ "incidents": [ ... ] }`}</code>.
        <br />
        <code>GET /incidents/{`{incident_id}`}</code> returns a single incident with its events,
        approvals, checkpoints, and trace links (<code>404</code> if not found).
      </p>

      <h2 id="run">Run the next step</h2>
      <p>
        <code>POST /incidents/{`{incident_id}`}/run</code> advances the incident one stage, invoking
        the agent via the gateway.
      </p>
      <pre>
        <code>{`{ "scenario": null, "force_mode": null, "demo_run": false }`}</code>
      </pre>
      <p>
        <code>force_mode</code> accepts <code>normal</code> | <code>degraded</code> |
        <code> blackout</code> to pin a mode.
      </p>

      <h2 id="approve">Approve an action</h2>
      <p>
        <code>POST /incidents/{`{incident_id}`}/approve</code> resolves a pending approval. On
        approval, the gated write executes through <code>jaguar-act</code> and the incident advances
        to verification.
      </p>
      <pre>
        <code>{`{ "approval_id": "apr_...", "approved": true, "note": "Approved — restart the worker." }`}</code>
      </pre>
      <p>
        Returns <code>{`{ "incident": { ... }, "approval": { ... } }`}</code>. There is also
        <code> POST /incidents/{`{incident_id}`}/sync-approvals</code> to reconcile approval state
        against the recommendation text and trace spans.
      </p>

      <h2 id="traces">Trace evidence</h2>
      <p>
        <code>GET /incidents/{`{incident_id}`}/traces</code> returns the trace summary surfaced in
        the war room — model resolved, span count, guardrails that fired, and the tools the agent
        called. See <a href="/docs/truefoundry">TrueFoundry + Bedrock</a>.
      </p>
    </DocPage>
  );
}
