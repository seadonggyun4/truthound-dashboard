# Deployment

## What this page covers

This page explains how to deploy Truthound Dashboard as an operational control-plane for
Truthound 3.0 and what to validate before you treat a deployment as production-ready.

## Before you start

- A compatible Python environment and package installation path.
- Access to the dashboard state database and artifact storage path.
- A deployment plan for the API, frontend shell, background tasks, and observability
  components used in your environment.

## UI path or entry point

Deployment is primarily a platform task. Use the dashboard UI only after the runtime is
healthy enough to create a session and load the overview.

## Step-by-step workflow

1. Install the dashboard package and runtime dependencies.
2. For review environments, treat Render as the canonical preview surface and serve the
   FastAPI app together with the bundled SPA from the same origin.
3. Configure the state database, artifact storage, and environment variables.
4. Run the shared preview build flow so the frontend bundle is copied into
   `src/truthound_dashboard/static` before the app starts.
5. Start the API and any required background services such as schedulers or queue
   workers.
6. Create a session and verify overview, observability, artifact generation, and
   incident triage flows.

## Expected outputs

- A reachable API and frontend shell.
- A same-origin preview environment where the browser route and `/api/v1` are served by
  the same FastAPI deployment.
- Healthy control-plane state storage.
- Successful session bootstrap and workspace loading.
- No dependency on removed mock or legacy surfaces.

## Failure modes and troubleshooting

- If a preview deployment fails during frontend dependency installation, verify that the
  platform is using `npm ci` and that `@typescript-eslint/eslint-plugin` and
  `@typescript-eslint/parser` are on the same version family.
- If preview builds emit `EBADENGINE` warnings for the lint toolchain, move the build
  environment to a current Node 20 LTS release or Node `22.13+` before treating the
  preview as stable.
- If deployment starts but sessions cannot be created, inspect configuration and
  database readiness before checking UI code.
- If artifacts cannot be generated, validate artifact storage and file permissions.
- If scheduled work fails after deployment, inspect the scheduler and notification
  stack separately from the main API process.

## Related APIs

- `GET /health`
- `GET /auth/session`
- `GET /overview`
- `GET /observability/*`

## Next steps

Continue with [Configuration](configuration.md) and
[State Storage and Migrations](state-storage-and-migrations.md).

## Canonical runtime and docs URLs

- Reviewer-facing application preview: `https://truthound-dashboard.onrender.com/`
- Dashboard docs: `https://truthound.netlify.app/dashboard/`
- Main docs portal: `https://truthound.netlify.app/`

Keep these roles separate in runbooks and checks. Render hosts the live dashboard
application preview. Netlify hosts the documentation portal and the staged
`/dashboard/` documentation section.

## Preview platform defaults

- Canonical reviewer preview: Render full-stack deployment from the repository root.
- Current shared preview URL: `https://truthound-dashboard.onrender.com/`
- Build command: `./scripts/build_preview.sh`
- Start command: `truthound-dashboard serve --host 0.0.0.0 --port $PORT --no-browser`
- Health endpoint: `GET /health`
- Preview environment defaults:
  - `TRUTHOUND_DATA_DIR=/opt/render/project/.preview-data`
  - `TRUTHOUND_LOG_LEVEL=info`
- Canonical preview does not set `VITE_API_URL`. The frontend defaults to same-origin
  `/api/v1` requests.
- Vercel is optional and non-blocking. If you keep it for manual static checks, keep the
  root at `frontend/` and the install step on `npm ci`.
- Do not use `https://truthound.netlify.app/dashboard/` for runtime validation. That
  host is for documentation, not the running preview app.

## Platform settings to update

### Render

- Repository root: `/`
- Blueprint file: `render.yaml`
- Build command: `bash ./scripts/build_preview.sh`
- Start command: `truthound-dashboard serve --host 0.0.0.0 --port $PORT --no-browser`
- Health check path: `/health`
- Environment defaults:
  - `TRUTHOUND_DATA_DIR=/opt/render/project/.preview-data`
  - `TRUTHOUND_LOG_LEVEL=info`
- Do not set `VITE_API_URL` for the canonical preview service.

### Vercel

- Remove Vercel from the reviewer-facing preview path. Disable automatic preview
  deployments or disconnect the app project entirely if Render is the canonical review
  environment.
- If you keep Vercel for occasional static verification:
  - Root directory: `frontend`
  - Install command: `npm ci`
  - Build command: the repository `frontend/vercel.json` value
  - Output directory: `dist`
  - Keep SPA rewrites enabled
  - Do not treat `VITE_API_URL` as the primary review configuration
