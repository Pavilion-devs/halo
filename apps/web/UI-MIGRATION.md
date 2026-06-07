# Halo UI Migration — Jaguar design system → Halo

Status doc + plan of record for adopting the **Jaguar** dashboard visual language for
**Halo** (resilient incident commander). Read this before touching the web app.

## Goal

Reuse Jaguar's design system (Tailwind v4 + the scoped `dashboard.css` system, green/light
SaaS look) and re-skin it as Halo. **Keep the visual system intact** — we relabel semantics
and rewire data, we do not redesign. Trading concepts become incident/resilience concepts.

- Source template: `/Users/olathepavilion/Documents/frontier/jaguar/apps/web`
- Target: `/Users/olathepavilion/Documents/halo/apps/web`
- Order (agreed): **Overview dashboard first, then War Room (incident detail).**
- Mode control: the top-right segmented switch is a **read-only live mode posture**
  (Normal / Degraded / Blackout), not an interactive filter.

## Stack delta

| | Jaguar | Halo (before) | Halo (after) |
|---|---|---|---|
| Styling | Tailwind v4 + scoped `dashboard.css` | plain CSS, serif theme | Tailwind v4 + `dashboard.css` (ported) |
| Icons | `lucide-react` + inline SVG | inline only | `lucide-react` + inline SVG |
| Fonts | Geist / Geist Mono (next/font) | none | Geist / Geist Mono (next/font) |
| Data | `@jaguar/*` workspace pkgs (Prisma) | FastAPI via `lib/api.ts` | FastAPI via `lib/api.ts` (unchanged) |

We **do not** port any `@jaguar/*` data packages. Every Jaguar `getX()` DB call is replaced
by Halo's existing `/incidents` API plus small derived selectors in `lib/dashboard.ts`.

## Styling isolation strategy

- Root `app/globals.css` (old serif theme) is **kept** and still imported by the root layout,
  so legacy routes (`/incidents/[id]`) stay readable until the War Room pass replaces them.
- New `app/theme.css` = Jaguar's `globals.css` (Tailwind import + `@theme` tokens). Imported
  only by the shell layout.
- New `app/dashboard.css` = Jaguar's `dashboard.css`, scoped under `.halo-dashboard` (renamed
  from `.jaguar-dashboard`), font literals repointed to `--font-geist-sans/-mono`. Imported by
  the shell layout.
- Geist is loaded in the root layout with **unique** variable names (`--font-geist-sans`,
  `--font-geist-mono`) to avoid colliding with the Tailwind `--font-sans` token.

## Routing

- `/` → redirect to `/dashboard`.
- `app/(shell)/` route group = sidebar + topbar chrome (light `.halo-dashboard` shell).
  - `app/(shell)/dashboard/page.tsx` — the ported overview.
- `app/incidents/[id]` — left in place (legacy serif) until the War Room pass moves it into
  the shell. Known interim: it will look plain, not broken.

## Jaguar → Halo mapping (overview)

Sidebar (`Jaguar` brand → `Halo`):

| Jaguar | Halo | Live this pass? |
|---|---|---|
| Dashboard | Dashboard | ✅ |
| Launches | Incidents | links to `/incidents` (legacy) |
| Analyst | Evidence | placeholder |
| Alerts | Alerts | placeholder |
| Scorecard | Traces | placeholder |
| Personas | Modes | placeholder |
| Settings | Settings | placeholder |

Top-right persona switch → **Mode posture** (read-only): system mode = most severe mode across
active incidents (blackout > degraded > normal), lit green / amber / red.

Dashboard cards (all derived from a single `/incidents` fetch unless noted):

| Jaguar element | Halo element | Source |
|---|---|---|
| Total Launches (dark hero) | **Active Incidents** | incidents not closed/handed_off |
| Calls Validated | **Failures Absorbed** | `mode.changed`→degraded/blackout + `truefoundry.invocation_failed` events |
| Open Calls | **Checkpoints Preserved** | Σ `checkpoint_index` |
| Ready to Enter | **Pending Approvals** | Σ approvals with status `pending` |
| Calls Issued · 7d (bar chart) | **Workflow Events · 7d** | all events bucketed by day |
| Latest call (+ Open launch) | **Active incident** (+ Open war room) | top active incident → `/incidents/{id}` |
| Watchlist | **Incidents** list | active incidents, dot = mode color |
| Recent Calls | **Recent activity** | cross-incident event feed, pill = mode/status |
| Win Rate gauge | **Continuity** gauge | % of incidents that never hit blackout; legend Normal/Degraded/Blackout |
| Worker Uptime (dark timer) | **Halo Uptime** | counts from earliest incident; "Live" from latest event |

Honesty notes:
- Model label must be read from the live trace summary (`model_name`), never hardcoded — the
  current route resolves to Bedrock **Opus**, not Sonnet.
- Stats are designed to read as intentional at small/zero values (e.g. "0 Pending Approvals",
  "0 unsafe actions reached prod").

## Component inventory (target `components/dashboard/`)

Ported ~verbatim (presentational): `stat-card`, `events-week-chart` (was conviction-week-chart),
`resilience-gauge` (was winrate-gauge), `halo-uptime` (was worker-uptime).
Rewired data/markup kept: `sidebar`, `topbar` + `halo-search` (simplified, no GoldRush),
`active-incident-card` (was reminder-card), `incidents-card` (was watchlist-card),
`recent-events-card` (was recent-calls-card), `mode-posture` (was persona-switcher).

## Checklist

- [x] Deps: tailwindcss, @tailwindcss/postcss, lucide-react + `postcss.config.mjs`
- [x] `app/theme.css` (Tailwind theme) + `app/dashboard.css` (scoped, renamed) + `app/halo.css` (mode colors)
- [x] Root `app/layout.tsx`: Geist fonts + Halo metadata
- [x] `app/(shell)/layout.tsx` + sidebar + topbar + search
- [x] `lib/dashboard.ts` selectors
- [x] `app/(shell)/dashboard/page.tsx` + ported card components
- [x] `/` redirect to `/dashboard`
- [x] `npm install` + `tsc --noEmit` clean + `next build` clean
- [x] Verified rendering against live API (18 real incidents, mode posture, spotlight, no runtime errors)
- [x] **War Room** (`app/(shell)/incidents/[id]`) — full interactive layout, verified

## War Room (done)

`/incidents/[id]` now lives in the shell and mirrors Jaguar's `launches/[id]` composition:
`page-head` + mode posture, 4 stats (ModeHero dark + Stage/Checkpoints/Failures), Halo's read
(`c-conviction`, memo styling), Operator console (`c-discovery`, Run + chaos + force-mode),
Trace evidence (`c-conviction`, real `model_name`/`span_count`/guardrail block), Approval gate
(`c-discovery`), and the Event timeline (`c-launches-full`).

- Interactive via server actions in `app/(shell)/incidents/[id]/actions.ts`
  (`runNextStep`, `resolveApproval`, `armChaos`) → POST to Halo API → `revalidatePath`.
- Helpers in `lib/war-room.ts` (stage index, event tone, trace shaping). `lib/api.ts` extended
  with `checkpoints[]`, `TraceSummary`, and `getIncidentTraces()`.
- New `/incidents` list page; legacy `app/incidents/[id]` + old root components removed.
- Verified against live API: the guardrail incident renders real trace evidence
  (`secrets-detection` → blocked, `claude-opus-4-6`, 55 spans); chaos arm returns `202`.
- Note: `next build` needs a clean `.next` after route changes (stale `/_error` trace).

## Polish (done 2026-06-03)
- **Auto-refresh:** Operator console + Approval gate call `router.refresh()` after each server
  action (canonical pattern, same as Jaguar's AgentMemoCard) so the page reflects new
  stage/mode/events/trace without a manual reload.
- **Nav footguns removed:** unbuilt sidebar items (Evidence/Alerts/Traces/Modes/Settings) render
  as disabled `<span>` + "soon" badge (no href, can't 404); topbar mail/bell are decorative buttons.

## Theme: dark monochrome (committed 2026-06-04)

Halo is **visually distinct from Jaguar** (which is now Halo's integration source, so they'd
otherwise look like the same app side-by-side in the demo). Decision: a **dark incident console**
with white "spotlight" hero cards and white controls, over a **semantic status palette**:
`indigo #6366F1` = degraded / active / accent, `green #22C55E` = normal / healthy,
`red #EF4444` = blackout / critical, `gray rgba(255,255,255,.25)` = resolved / neutral. (Color on
screen = a status, never decoration.) Implemented as an override layer `app/halo-theme.css` (scoped
`.halo-dashboard`), imported last in the shell layout after `theme.css`/`dashboard.css`/`halo.css`,
so the ported Jaguar base stays pristine. To re-skin, edit that one file.

Nav: the active sidebar item uses a subtle white fill (`rgba(255,255,255,.07)`), no left bar/glow.

- Two element colours were made theme-driven so nothing stayed hardcoded green: the Continuity
  gauge (`--gauge-arc`/`--gauge-arc-2` in `continuity-gauge.tsx`) and the activity avatars
  (`--evt-av-*` in `recent-events-card.tsx`), both with green fallbacks.
- A light-indigo alternative was prototyped and rejected (too close to Jaguar). Mockup theme files
  removed.

## Remaining polish ideas (optional)
- Build out the disabled nav destinations (Evidence = product-data tools, Traces = span explorer).
- Checkpoint ladder panel; trace span waterfall.
- Opus→Sonnet virtual-model route is **optional cleanup**, not a blocker (Bedrock is proven; the
  UI already reads the real `model_name` from the trace, so it stays truthful either way).

## Bigger open thread (not UI): make the data real
The resilience engine is real (Bedrock, guardrails, traces, mode downgrade), but the incident
**evidence** is still hardcoded fixtures in `apps/api/app/services/product_data.py`. Next major
step is swapping those for real read-only adapters to a real product (**Jaguar** is the chosen
target — it has a real failure mode: its worker goes offline). Read real, keep writes
approval-gated.

## Known interim notes (overview pass)

- `/incidents/[id]` still renders the legacy serif components until the War Room pass.
- `theme.css` (Tailwind) is wired but only lightly used; it's set up for the War Room.
- "Workflow Events · 7d" looks sparse when real events cluster on one day — expected; it
  fills in as incidents run across days.
</content>
