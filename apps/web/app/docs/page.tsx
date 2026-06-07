import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "the-problem", label: "The problem" },
  { id: "what-halo-does", label: "What Halo does" },
  { id: "a-real-run", label: "A real run" },
  { id: "next-steps", label: "Next steps" }
];

export default function IntroductionPage() {
  return (
    <DocPage
      eyebrow="Overview"
      title="Halo"
      description="A resilient incident commander — an agent built to stay standing when its own infrastructure breaks."
      toc={toc}
    >
      <Callout>
        Built for the TrueFoundry <strong>Resilient Agents</strong> hackathon on AWS Bedrock.
        Halo runs against a real live product (Jaguar), not a toy.
      </Callout>

      <h2 id="the-problem">The problem</h2>
      <p>
        Agents fall apart the moment their infrastructure does. A model starts rate-limiting, a
        tool times out, a provider has a bad day — and the agent either crashes, starts making
        things up, or quietly does the wrong thing. That is especially painful during an incident,
        because the one tool you are leaning on to recover just became another thing that is down.
      </p>

      <h2 id="what-halo-does">What Halo does</h2>
      <p>
        Halo is an incident commander that is built to stay standing when things break. It works
        real incidents on a live product through TrueFoundry&apos;s AI Gateway and MCP Gateway, and
        instead of failing it <strong>degrades</strong>.
      </p>
      <ul>
        <li>
          <strong>Investigates, doesn&apos;t guess.</strong> Pulls live worker status, ingestion,
          deploys, and failures through the product&apos;s MCP tools and works out the real root cause.
        </li>
        <li>
          <strong>Asks before it acts.</strong> Risky actions are split onto a separate write
          server and never run without human approval.
        </li>
        <li>
          <strong>Degrades instead of dying.</strong> On a rate-limit or outage it fails over to a
          backup model and steps down a mode — cheaper model, read-only tools — instead of crashing.
        </li>
        <li>
          <strong>Tells the truth.</strong> After a fix runs, it re-checks the product and reports
          whether the action actually worked — no premature victory laps.
        </li>
      </ul>

      <h2 id="a-real-run">A real run</h2>
      <p>
        In our demo run, Halo diagnosed a real Jaguar worker blackout, prepared a worker restart,
        and — once an operator approved it — executed it on the live VPS through Jaguar&apos;s
        ops-runner. Then it checked its own work and reported the truth: the restart was necessary
        but it was not the whole fix. The real culprit was an upstream credential that had been
        invalidated.
      </p>
      <p>
        Nothing dangerous ran without a human, nothing sensitive slipped through a guardrail, and
        the whole run is backed by TrueFoundry traces.
      </p>

      <h2 id="next-steps">Next steps</h2>
      <ul>
        <li>
          <a href="/docs/architecture">Architecture</a> — the monorepo, the read/write MCP split,
          the approval gate, and checkpoints.
        </li>
        <li>
          <a href="/docs/resilience">Resilience &amp; modes</a> — fallback routing and the
          normal → degraded → blackout ladder.
        </li>
        <li>
          <a href="/docs/truefoundry">TrueFoundry + Bedrock</a> — exactly which gateway features we
          used and how.
        </li>
      </ul>
    </DocPage>
  );
}
