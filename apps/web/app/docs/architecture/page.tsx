import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "monorepo", label: "Monorepo layout" },
  { id: "components", label: "Components" },
  { id: "the-workflow", label: "The workflow" },
  { id: "checkpoints", label: "Checkpoints" }
];

export default function ArchitecturePage() {
  return (
    <DocPage
      eyebrow="How it works"
      title="Architecture"
      description="A clear split between the operator UI, the workflow engine, and the gateway that everything routes through."
      toc={toc}
    >
      <h2 id="monorepo">Monorepo layout</h2>
      <table>
        <thead>
          <tr>
            <th>Path</th>
            <th>What it is</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>apps/web</code></td>
            <td>The operator UI — Next.js 15 / React 19 / Tailwind 4. Landing page, dashboard, and the incident war room.</td>
          </tr>
          <tr>
            <td><code>apps/api</code></td>
            <td>The workflow engine — FastAPI + SQLModel/SQLite (Python 3.12). Runs the workflow, talks to the gateway, persists checkpoints.</td>
          </tr>
          <tr>
            <td><code>infra/</code></td>
            <td>Deploy and live-setup config, including the documented real run.</td>
          </tr>
        </tbody>
      </table>

      <h2 id="components">Components</h2>
      <p>
        The product is reached <strong>only</strong> through MCP, and every model call goes through
        the TrueFoundry gateway. That single chokepoint is what makes routing, fallback, guardrails,
        and observability enforceable in one place.
      </p>
      <ul>
        <li>
          <strong>Workflow engine</strong> — drives the staged incident workflow, mode transitions,
          checkpointing, and approvals.
        </li>
        <li>
          <strong>Operator war room</strong> — renders Halo&apos;s read, the trace evidence (model,
          spans, guardrails, tools), the event timeline, and the approval gate.
        </li>
        <li>
          <strong>MCP tool servers</strong> — two virtual servers: <code>jaguar-observe</code> (read)
          and <code>jaguar-act</code> (write). See <a href="/docs/guardrails">Guardrails &amp; safety</a>.
        </li>
        <li>
          <strong>Persistence</strong> — incidents, events, approvals, checkpoints, and trace links,
          so a run is durable and resumable.
        </li>
      </ul>

      <h2 id="the-workflow">The workflow</h2>
      <p>Every incident runs through an explicit workflow:</p>
      <ul>
        <li><strong>Detect &amp; diagnose</strong> — gather live evidence through read tools, line it up against the deploy timeline, match a runbook.</li>
        <li><strong>Decide with a human</strong> — prepare a recovery action and hold it at the approval gate.</li>
        <li><strong>Execute</strong> — on approval, run the action through the write server.</li>
        <li><strong>Verify</strong> — re-check the product and report whether the fix actually held.</li>
      </ul>

      <h2 id="checkpoints">Checkpoints</h2>
      <p>
        Every stage persists a checkpoint, so the agent&apos;s state is durable: a run resumes from
        its current stage instead of restarting — which matters precisely when something failed
        mid-incident.
      </p>

      <Callout>
        Nothing in Halo is Jaguar-specific. It reaches the product only through the MCP Gateway, so
        connecting a different product is configuration plus a thin action adapter — the mode ladder,
        approval gate, checkpoints, and self-verification all work unchanged.
      </Callout>
    </DocPage>
  );
}
