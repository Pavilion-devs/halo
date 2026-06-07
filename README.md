# Halo

**A resilient incident commander agent — it keeps operating when the systems around it degrade.**

![Halo war room](image.png)

Halo investigates live production incidents on a real product, gathers evidence through governed tools, reasons over it with a fallback-capable model stack, and puts risky recovery actions behind human approval — then checks whether the action actually fixed the problem. When providers rate-limit, time out, or fail, Halo drops to a safer operating mode instead of crashing.

Built for the TrueFoundry **Resilient Agents** hackathon on AWS Bedrock.

## What makes it different

Most agents bolt resilience on afterward. In Halo, resilience *is* the product:

- **Adaptive operating modes** — `Normal → Degraded → Blackout`. Under failure Halo downgrades to a cheaper/faster model and a read-only toolset, and keeps making progress instead of stopping.
- **Everything is governed** — all model calls route through TrueFoundry AI Gateway → Bedrock (with priority-based fallback); all tools go through MCP Gateway, split into read-only (`jaguar-observe`) and write (`jaguar-act`); guardrails screen model and tool I/O.
- **Risky actions are gated** — Halo *prepares* an action (e.g. a worker restart) but only executes it after a human approves, forwarded through the live ops path.
- **State is preserved** — an explicit 8-stage workflow checkpoints after each stage, so an incident resumes from saved state rather than restarting.
- **It's provable** — every run leaves a TrueFoundry trace (resolved model, span count, guardrail hits, MCP tools used), surfaced directly in the war room.

## Architecture

```
apps/web    Next.js dashboard + war room — incident view, trace evidence, approvals
apps/api    FastAPI workflow engine — incident state machine, mode logic, TrueFoundry + ops integration
infra       TrueFoundry config (agents, virtual MCP servers, guardrails), prompts, OpenAPI specs
```

- **Models** — AWS Bedrock via TrueFoundry virtual models: `halo-vm-normal` (Claude, with fallback) and `halo-vm-degraded` (Claude Haiku), priority-routed.
- **Tools** — MCP Gateway, with `jaguar-observe` (read) and `jaguar-act` (approval-gated write) virtual servers.
- **Guardrails** — secrets/PII detection on model input/output and tool results.
- **Persistence** — SQLite via SQLModel (override with `HALO_DATABASE_URL`).

## Quickstart

**API** — Python 3.12:

```bash
cd apps/api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Web** — Node:

```bash
cd apps/web
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open http://127.0.0.1:3000. The web app talks to the API at `http://127.0.0.1:8000` (override with `NEXT_PUBLIC_API_BASE_URL`).

To connect TrueFoundry/Bedrock and the live ops tools, fill in `apps/api/.env` — see `infra/deploy/backend.env.example`.

## API

```
GET  /health                  liveness
GET  /readiness               config snapshot (active MCP servers, guardrails)
POST /incidents               create an incident
GET  /incidents               list incidents
GET  /incidents/{id}          incident detail (events, checkpoints, approvals, traces)
POST /incidents/{id}/run      advance one workflow stage (invokes the agent)
POST /incidents/{id}/approve  resolve an approval (forwards to the live ops path)
GET  /incidents/{id}/traces   TrueFoundry trace summary for the incident
```

## Stack

Next.js 15 · React 19 · Tailwind 4 · TypeScript · FastAPI · SQLModel · TrueFoundry AI + MCP Gateway · AWS Bedrock
