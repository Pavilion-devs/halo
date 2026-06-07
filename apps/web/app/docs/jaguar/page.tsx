import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "what-is-jaguar", label: "What Jaguar is" },
  { id: "over-mcp", label: "Reaching it over MCP" },
  { id: "read-write-split", label: "The read / write split" },
  { id: "tools", label: "Tools Halo uses" },
  { id: "act-path", label: "The approval bridge" },
  { id: "mode-aware", label: "Mode-aware access" }
];

export default function JaguarPage() {
  return (
    <DocPage
      eyebrow="How it works"
      title="Jaguar integration"
      description="Halo doesn't run against a sandbox. It commands incidents on Jaguar — a real, live product — reached entirely through the MCP Gateway."
      toc={toc}
    >
      <h2 id="what-is-jaguar">What Jaguar is</h2>
      <p>
        <strong>Jaguar</strong> is a real, deployed product (<code>jaguaralpha.xyz</code>) — workers,
        ingestion, deploys, and all. Halo treats it as the subject of an incident: it reads Jaguar&apos;s
        live state to diagnose what broke, and — only behind a human approval gate — acts on Jaguar to
        recover it. The point of running against something live rather than a toy is that the failure
        modes are real: a worker actually falls over, a deploy actually regresses, an upstream
        credential actually expires.
      </p>

      <h2 id="over-mcp">Reaching it over MCP</h2>
      <p>
        Halo never imports a Jaguar SDK or calls its REST API directly. The product is reached
        <strong> only</strong> through MCP. Jaguar&apos;s MCP server is registered in the TrueFoundry
        MCP Gateway as a remote endpoint:
      </p>
      <pre>
        <code>https://www.jaguaralpha.xyz/api/mcp</code>
      </pre>
      <p>
        Alongside it, Halo&apos;s own incident and runbook APIs are turned into tools with
        OpenAPI-to-MCP (<code>incident-api</code>, <code>runbooks-api</code>). Everything the agent can
        see or touch is therefore a governed MCP tool behind the gateway — which is what makes the read
        / write split, guardrails, and tracing enforceable in one place.
      </p>

      <h2 id="read-write-split">The read / write split</h2>
      <p>
        The Jaguar tools are split across <strong>two virtual MCP servers</strong>, so an agent&apos;s
        capability is decided by which server it gets handed — not by trusting the model to behave:
      </p>
      <table>
        <thead>
          <tr>
            <th>Virtual server</th>
            <th>Boundary</th>
            <th>What it grants</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>jaguar-observe</code></td>
            <td>Read-only</td>
            <td>Health, deploys, errors, incident context, status events, runbooks. No way to mutate Jaguar.</td>
          </tr>
          <tr>
            <td><code>jaguar-act</code></td>
            <td>Approval-gated writes</td>
            <td>A tightly scoped set of recovery actions, each held at the approval gate before it runs.</td>
          </tr>
        </tbody>
      </table>
      <p>
        The servers are curated, not wide-open: the chaos / fault-injection tools Jaguar exposes
        (<code>failNextCall</code>, <code>delayNextCall</code>, <code>returnBadPayload</code>), deletes,
        and shell-style tools are excluded from both servers entirely.
      </p>

      <h2 id="tools">Tools Halo uses</h2>
      <p>The read path is deliberately small and specific:</p>
      <ul>
        <li><code>getHealthSummary</code> — current worker / service health.</li>
        <li><code>getRecentDeploys</code> — the deploy timeline to line failures up against.</li>
        <li><code>getTopErrors</code> — the loudest current errors.</li>
        <li><code>getIncidentContext</code> — incident-scoped state for the run.</li>
        <li><code>getRecentStatusEvents</code> — recent status transitions.</li>
        <li><code>searchRunbooks</code> / <code>getRunbook</code> — match the symptoms to a known runbook.</li>
      </ul>
      <p>
        Halo gathers this evidence, lines it up against the deploy timeline, and works out the
        <em> actual</em> root cause before it proposes anything — see{" "}
        <a href="/docs/architecture">Architecture</a> for the full workflow.
      </p>

      <h2 id="act-path">The approval bridge</h2>
      <p>
        Writes never go straight from the model to Jaguar. The agent <em>drafts</em> a recovery action
        (for example, a worker restart) and parks it at the approval gate. When an operator approves it
        in the war room, Halo&apos;s backend — not the model — calls the Jaguar MCP endpoint directly to
        resolve it, as a JSON-RPC <code>tools/call</code>:
      </p>
      <ul>
        <li><code>approve_action</code> on approve, <code>reject_action</code> on reject.</li>
        <li>
          Authenticated with a Bearer API key <strong>plus</strong> a separate
          <code> X-Operator-Secret</code> header — so executing a real action needs a credential the
          model never holds.
        </li>
        <li>Bounded by a short timeout, with HTTP / transport errors surfaced as a clean failure rather than a guess.</li>
      </ul>
      <p>This bridge is configured with a handful of environment variables on the API:</p>
      <pre>
        <code>{`HALO_JAGUAR_MCP_URL=https://www.jaguaralpha.xyz/api/mcp
HALO_JAGUAR_MCP_API_KEY=...
HALO_JAGUAR_OPERATOR_SECRET=...
HALO_JAGUAR_ACTION_TIMEOUT_SECONDS=20`}</code>
      </pre>

      <h2 id="mode-aware">Mode-aware access</h2>
      <p>
        Which Jaguar server the agent gets is tied to Halo&apos;s operating mode. In <strong>Normal</strong>
        it has <code>jaguar-observe</code> plus the approval-gated <code>jaguar-act</code>. When Halo steps
        down to <strong>Degraded</strong> or <strong>Blackout</strong>, it is handed the observe server
        only — it can keep investigating, but it structurally cannot write to the live product when it&apos;s
        no longer safe to act. See <a href="/docs/resilience">Resilience &amp; modes</a>.
      </p>

      <Callout>
        None of this is hard-coded to Jaguar. Because the product is reached only through the MCP Gateway,
        pointing Halo at a different product is a config change — register its MCP server, curate an observe
        / act split — plus a thin action adapter. The mode ladder, approval gate, and self-verification all
        work unchanged.
      </Callout>
    </DocPage>
  );
}
