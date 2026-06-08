import { DocPage, Callout, type TocItem } from "@/components/docs/doc-page";

const toc: TocItem[] = [
  { id: "where-it-runs", label: "Where it runs" },
  { id: "backend-railway", label: "Backend on Railway" },
  { id: "frontend-vercel", label: "Frontend on Vercel" },
  { id: "how-they-connect", label: "How they connect" },
  { id: "state", label: "State & demo data" }
];

export default function DeploymentPage() {
  return (
    <DocPage
      eyebrow="Platform & deployment"
      title="Deployment"
      description="Halo is live, not a localhost demo: the FastAPI backend runs on Railway and the Next.js web app runs on Vercel."
      toc={toc}
    >
      <h2 id="where-it-runs">Where it runs</h2>
      <p>The monorepo splits cleanly into two independently deployed services:</p>
      <table>
        <thead>
          <tr>
            <th>Service</th>
            <th>Path</th>
            <th>Host</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Web app (landing, dashboard, war room, these docs)</td>
            <td><code>apps/web</code></td>
            <td><strong>Vercel</strong></td>
          </tr>
          <tr>
            <td>Workflow API (state machine, mode logic, gateway calls)</td>
            <td><code>apps/api</code></td>
            <td><strong>Railway</strong></td>
          </tr>
        </tbody>
      </table>
      <p>
        The live app is at <a href="https://haloagent.xyz">haloagent.xyz</a>, and this documentation
        is served from the same deployment at <code>/docs</code>.
      </p>

      <h2 id="backend-railway">Backend on Railway</h2>
      <p>
        The API deploys from <code>apps/api</code> (Railway <strong>Root Directory =
        <code> apps/api</code></strong>) using the in-repo <code>Dockerfile</code>. On every boot the
        container creates its tables, seeds the demo incidents, and then starts Uvicorn bound to
        Railway&apos;s injected <code>$PORT</code>:
      </p>
      <pre>
        <code>{`python -c "import app.db.models; from app.db.session import create_db_and_tables; create_db_and_tables()" \\
  && python scripts/seed_resilience_demo.py \\
  && python scripts/seed_live_approval_demo.py \\
  && uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000}`}</code>
      </pre>
      <p>
        Railway exposes it on a public HTTPS URL (for example
        <code> https://halo-api-production.up.railway.app</code>). Configuration — the TrueFoundry
        gateway URL, saved-agent IDs, and the Jaguar action bridge — comes from environment variables;
        see <a href="/docs/run-locally">Run it locally</a> for the full list.
      </p>

      <h2 id="frontend-vercel">Frontend on Vercel</h2>
      <p>
        The web app deploys from <code>apps/web</code> (Vercel <strong>Root Directory =
        <code> apps/web</code></strong>) as a standard Next.js 15 project. It needs exactly one
        environment variable to find the backend:
      </p>
      <pre>
        <code>NEXT_PUBLIC_API_BASE_URL=https://&lt;your-railway-url&gt;</code>
      </pre>
      <p>
        Because it is a <code>NEXT_PUBLIC_</code> variable it is baked in at build time, so it has to
        be set <em>before</em> the build. If it is unset, the app falls back to{" "}
        <code>http://127.0.0.1:8000</code> for local development.
      </p>

      <h2 id="how-they-connect">How they connect</h2>
      <p>
        All of the frontend&apos;s API calls run <strong>server-side</strong> — from server components
        and server actions — so the browser never talks to the backend directly. That means the two
        services only need the Railway URL wired into Vercel; <strong>no CORS setup is required</strong>
        for the app to work. The backend just has to be reachable from Vercel over HTTPS.
      </p>

      <h2 id="state">State &amp; demo data</h2>
      <p>
        The API uses SQLite, which is <strong>ephemeral</strong> on Railway — the file is wiped on every
        redeploy or restart. That is intentional: the boot command reseeds the demo incidents each time,
        so the deployment always comes up in a clean, known state. Don&apos;t attach a volume expecting
        persistence.
      </p>

      <Callout>
        Right now everything is up: the backend is running on Railway and the frontend on Vercel, wired
        together through <code>NEXT_PUBLIC_API_BASE_URL</code> — open{" "}
        <a href="https://haloagent.xyz">haloagent.xyz</a> and the dashboard lists live incidents straight
        from the Railway API.
      </Callout>
    </DocPage>
  );
}
