import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "prerequisites", label: "Prerequisites" },
  { id: "the-api", label: "Run the API" },
  { id: "the-web-app", label: "Run the web app" },
  { id: "the-demo-incident", label: "The demo incident" }
];

export default function RunLocallyPage() {
  return (
    <DocPage
      eyebrow="Overview"
      title="Run it locally"
      description="Halo is a monorepo: a FastAPI workflow engine and a Next.js operator UI. Here is how to bring both up."
      toc={toc}
    >
      <h2 id="prerequisites">Prerequisites</h2>
      <ul>
        <li>Python 3.12 and Node.js 18+.</li>
        <li>
          A TrueFoundry account with the AI Gateway configured (virtual models, MCP servers,
          guardrails). See <a href="/docs/truefoundry">TrueFoundry + Bedrock</a>.
        </li>
      </ul>

      <h2 id="the-api">Run the API</h2>
      <p>
        The workflow engine lives in <code>apps/api</code> (FastAPI + SQLModel/SQLite). It reads
        its config from <code>apps/api/.env</code>.
      </p>
      <pre>
        <code>{`cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000`}</code>
      </pre>
      <p>
        The API serves interactive OpenAPI docs at <code>http://127.0.0.1:8000/docs</code>.
      </p>

      <h2 id="the-web-app">Run the web app</h2>
      <p>
        The operator UI lives in <code>apps/web</code> (Next.js 15 / React 19 / Tailwind 4). It
        talks to the API and renders the landing page, the dashboard, and the incident war room.
      </p>
      <pre>
        <code>{`cd apps/web
npm install
npm run dev   # http://127.0.0.1:3000`}</code>
      </pre>

      <Callout>
        Run a <strong>single</strong> web dev server at a time. Two <code>next dev</code> processes
        share the same <code>.next</code> cache and can corrupt it.
      </Callout>

      <h2 id="the-demo-incident">The demo incident</h2>
      <p>
        A seed script creates a deterministic incident sitting at the approval gate, so you can open
        it and click <strong>Approve</strong> to watch the executed → verified flow:
      </p>
      <pre>
        <code>{`cd apps/api
./.venv/bin/python scripts/seed_live_approval_demo.py`}</code>
      </pre>
      <p>
        Re-run it to reset the incident — clicking Approve consumes it. Then open
        <code>/incidents/inc_demo_approval</code> in the web app.
      </p>
    </DocPage>
  );
}
