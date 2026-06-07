import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "the-three-modes", label: "The three operating modes" },
  { id: "model-fallback", label: "Model fallback" },
  { id: "the-mode-ladder", label: "The mode ladder" }
];

export default function ResiliencePage() {
  return (
    <DocPage
      eyebrow="How it works"
      title="Resilience & modes"
      description="The point of the design is what happens when things go wrong — so resilience is built into both the routing and the workflow."
      toc={toc}
    >
      <Callout>
        Halo&apos;s resilience mostly lives in <strong>gateway configuration</strong>, not in agent
        code. Failover and routing are enforced at the gateway; the workflow just reacts to it.
      </Callout>

      <h2 id="the-three-modes">The three operating modes</h2>
      <table>
        <thead>
          <tr>
            <th>Mode</th>
            <th>Behaviour</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Normal</strong></td>
            <td>Best model, full read + write (approval-gated) tools, multi-step investigation.</td>
          </tr>
          <tr>
            <td><strong>Degraded</strong></td>
            <td>When the primary model or a tool keeps failing, Halo falls back to a faster/cheaper model and a read-only toolset — and keeps going.</td>
          </tr>
          <tr>
            <td><strong>Blackout</strong></td>
            <td>When it is no longer safe to act, Halo stops writes, preserves state, and produces a clean handoff to a human.</td>
          </tr>
        </tbody>
      </table>

      <h2 id="model-fallback">Model fallback</h2>
      <p>
        Halo defines virtual models on the gateway, priority-routed to AWS Bedrock targets.
        <code>halo-vm-normal</code> is the primary Claude with a fallback target behind it;
        <code>halo-vm-degraded</code> is the faster/cheaper model used under stress.
      </p>
      <p>
        On a rate-limit, timeout, or 5xx, the gateway fails over to the next target automatically —
        with <strong>no</strong> retry or failover logic in the agent itself. This is what lets Halo
        degrade instead of die.
      </p>

      <h2 id="the-mode-ladder">The mode ladder</h2>
      <p>The mode ladder is driven by failures:</p>
      <ul>
        <li>Repeated rate-limits / timeouts / 5xx from the gateway step the agent down <code>normal → degraded</code>.</li>
        <li>Continued failure escalates <code>degraded → blackout</code>, where all writes stop and the incident is handed off.</li>
      </ul>
      <p>
        In degraded mode Halo is restricted to the read-only MCP server, so write capability is not
        even on the table when the agent is operating under stress. See
        <a href="/docs/guardrails"> Guardrails &amp; safety</a>.
      </p>
    </DocPage>
  );
}
