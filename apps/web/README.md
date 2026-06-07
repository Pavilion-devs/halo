# Halo Web

Next.js TypeScript dashboard shell for the Halo incident commander.

## Local Development

```bash
npm install
npm run dev
```

The app reads `NEXT_PUBLIC_API_BASE_URL` and defaults to `http://localhost:8000`.

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Demo fallback data is disabled by default. Enable it explicitly with:

```bash
NEXT_PUBLIC_ENABLE_DEMO_DATA=true npm run dev
```

## Current Scope

- Incident list
- Incident detail screen
- Timeline panel
- Mode badge
- Approvals placeholder
- Traces placeholder

The UI uses API data when available. If the API fails and demo mode is off, it shows an explicit error/empty state instead of silently masking the failure.
