import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "read-write-split", label: "Read / write tool isolation" },
  { id: "approval-gate", label: "The human approval gate" },
  { id: "secrets-detection", label: "Secrets-detection guardrail" }
];

export default function GuardrailsPage() {
  return (
    <DocPage
      eyebrow="How it works"
      title="Guardrails & safety"
      description="Halo's safety isn't a prompt instruction — it's enforced by the topology: isolated tools, an approval gate, and an inline guardrail."
      toc={toc}
    >
      <Callout>
        The approval gate and the read/write split are enforced at the <strong>gateway</strong>, not
        asked for in a prompt — so a wrong model output cannot reach production even if the agent
        decides to try.
      </Callout>

      <h2 id="read-write-split">Read / write tool isolation</h2>
      <p>
        The product&apos;s tools are split across two separate MCP servers at the gateway:
      </p>
      <ul>
        <li><code>jaguar-observe</code> — read-only tools (status, diagnostics, deploys, failures).</li>
        <li><code>jaguar-act</code> — write tools (the actions that change production).</li>
      </ul>
      <p>
        In <strong>degraded</strong> mode, Halo is restricted to the read server. Write capability
        simply is not available when the agent is operating under stress.
      </p>

      <h2 id="approval-gate">The human approval gate</h2>
      <p>
        Anything that writes has to clear a human approval before it runs. The action is registered
        as a pending approval; the incident sits in <code>waiting_for_approval</code> until an
        operator approves or rejects. Only on approval does the write execute through
        <code> jaguar-act</code>.
      </p>
      <p>
        This is the gate you see in the war room: Halo prepares a worker restart, but it will not
        touch production on its own.
      </p>

      <h2 id="secrets-detection">Secrets-detection guardrail</h2>
      <p>
        A <strong>secrets-detection</strong> guardrail runs inline at the gateway. In one incident
        the notes contained a token; the guardrail caught and blocked the call without us writing any
        detection logic, and Halo dropped into a safer mode rather than breaking.
      </p>
      <p>
        Security becomes a gateway policy rather than application code — and the block shows up as
        real trace evidence in the UI. See <a href="/docs/truefoundry">TrueFoundry + Bedrock</a>.
      </p>
    </DocPage>
  );
}
