import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "model-gateway", label: "Model Gateway" },
  { id: "virtual-models", label: "Virtual Models" },
  { id: "mcp-gateway", label: "MCP Gateway" },
  { id: "guardrails", label: "Guardrails" },
  { id: "observability", label: "Observability" }
];

export default function TrueFoundryPage() {
  return (
    <DocPage
      eyebrow="Platform & deployment"
      title="TrueFoundry + AWS Bedrock"
      description="The AI Gateway is the control plane for everything Halo does — every model call, every tool call, every guardrail."
      toc={toc}
    >
      <h2 id="model-gateway">Model Gateway</h2>
      <p>
        Every LLM call routes through the gateway to <strong>AWS Bedrock</strong>. Nothing talks to
        a model directly. This is what makes the rest of the resilience story possible — routing,
        fallback, and observability are all enforced at one layer.
      </p>

      <h2 id="virtual-models">Virtual Models</h2>
      <p>Halo defines two virtual models, priority-routed to Bedrock targets:</p>
      <table>
        <thead>
          <tr>
            <th>Virtual model</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>halo-vm-normal</code></td>
            <td>Primary Claude on Bedrock <strong>with a fallback target</strong> behind it.</td>
          </tr>
          <tr>
            <td><code>halo-vm-degraded</code></td>
            <td>A faster / cheaper model used when Halo steps down a mode.</td>
          </tr>
        </tbody>
      </table>
      <p>
        On a rate-limit, timeout, or 5xx, the gateway fails over to the next target automatically and
        the backend steps the agent down a mode. See <a href="/docs/resilience">Resilience &amp; modes</a>.
      </p>

      <h2 id="mcp-gateway">MCP Gateway</h2>
      <p>
        The same gateway governs the product&apos;s tools, exposed as two virtual MCP servers —
        <code> jaguar-observe</code> (read-only) and <code>jaguar-act</code> (approval-gated writes).
        Splitting the tools across two servers gives per-server governance out of the box.
      </p>

      <h2 id="guardrails">Guardrails</h2>
      <p>
        A <strong>secrets-detection</strong> guardrail runs inline at the gateway, blocking sensitive
        input before it reaches a model — with no detection logic in our code. See
        <a href="/docs/guardrails"> Guardrails &amp; safety</a>.
      </p>

      <h2 id="observability">Observability</h2>
      <p>
        Every step leaves a trace. Halo surfaces it right in the war room: which model resolved, how
        many spans the run produced, which guardrails fired, and exactly which tools the agent
        called. That is the audit trail that lets us prove a run happened rather than just claim it.
      </p>

      <Callout>
        Heads-up from building on it: the spans query API was occasionally slow, so for the live demo
        Halo serves a cached trace summary instead of issuing a live span query mid-incident — keeping
        the demo deterministic.
      </Callout>
    </DocPage>
  );
}
