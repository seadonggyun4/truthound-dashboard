# Configuration

## What this page covers

This page explains the configuration areas that matter most for day-two operations:
session bootstrap, database access, secret handling, artifact storage, queue behavior,
and observability.

## Before you start

- Access to the deployment environment variables or config layer.
- A clear separation between local, staging, and production values.
- Agreement on who owns secret rotation and artifact retention in your organization.

## UI path or entry point

Most configuration happens outside the UI. The dashboard surfaces configuration effects
through overview, observability, and runtime behavior rather than as a single giant
settings page.

## Step-by-step workflow

1. Set the database and storage configuration for the deployment.
2. Configure the bootstrap password or session authentication inputs.
3. Confirm the secret encryption setup so `secret_refs` can be persisted and resolved.
4. Validate notification and queue-related runtime settings if incidents or channel
   delivery are part of the deployment.
5. Confirm preview-specific defaults so reviewer environments behave like the
   single-origin application deployment.
6. Confirm observability settings and any logging or metrics integrations.

## Expected outputs

- Reproducible configuration across environments.
- A deployment where sources, notifications, artifacts, and sessions behave
  consistently.
- Preview environments that do not require split-origin frontend API wiring.

## Failure modes and troubleshooting

- If configuration changes appear to do nothing, confirm that the affected process was
  restarted and that the active environment matches the expected one.
- If only secret-backed features fail, inspect encryption and storage settings before
  assuming application-level bugs.
- If preview UI requests start failing only in hosted review environments, inspect
  `VITE_API_URL` first. Canonical preview should leave it unset so the app stays on
  same-origin `/api/v1`.

## Related APIs

- `GET /auth/session`
- `GET /observability/settings`
- `PUT /observability/settings`

## Next steps

Continue with [Security and Secrets](security-and-secrets.md).

## Preview configuration defaults

- Hosted reviewer preview URL: `https://truthound-dashboard.onrender.com/`
- Dashboard docs URL: `https://truthound.netlify.app/dashboard/`
- Leave `VITE_API_URL` unset for the canonical Render preview deployment.
- Keep `TRUTHOUND_DATA_DIR` on an ephemeral preview path unless you explicitly need
  state to persist across preview redeploys.
- Prefer `TRUTHOUND_LOG_LEVEL=info` in previews so reviewers can inspect runtime
  behavior without the noise of full debug logging.
- Use `npm ci` for any frontend install step in CI, Render, or optional Vercel checks.
- Use the Render URL for runtime checks and the Netlify URL for docs-only verification.
