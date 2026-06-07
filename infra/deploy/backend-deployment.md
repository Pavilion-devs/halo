# Halo Backend Deployment

## Production Launch Command

The FastAPI entrypoint is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Docker Build

Build from the repository root:

```bash
docker build -f apps/api/Dockerfile -t halo-api:latest .
```

Run locally:

```bash
docker run --rm -p 8000:8000 --env-file infra/deploy/backend.env.example halo-api:latest
```

Do not use `backend.env.example` with real secrets committed in it. Copy it to a local
or platform-managed environment file and inject secrets through the deployment platform.

## TrueFoundry Service Deployment

If deploying through TrueFoundry UI:

1. Create a Service deployment.
2. Use the repository root as build context.
3. Use `apps/api/Dockerfile`.
4. Expose port `8000`.
5. Set environment variables from `infra/deploy/backend.env.example`.
6. Configure health/readiness checks:
   - `GET /health`
   - `GET /readiness`
7. Ensure the service has an external URL reachable by TrueFoundry AI Gateway.

If deploying with `tfy apply`, first create the service in the UI and copy the generated
YAML, then replace the image/build/env sections with this Dockerfile and env set. This
avoids guessing undocumented service manifest fields.

## Temporary Tunnel For Demo Validation

If a durable deployment is not available, a temporary ngrok tunnel can validate MCP
reachability:

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
ngrok http 8000
HALO_PUBLIC_API_BASE_URL=https://<ngrok-host> ./infra/deploy/validate-public-api.sh
```

This is not a production deployment. The URL changes when the tunnel restarts.
