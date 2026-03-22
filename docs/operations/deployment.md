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
2. Configure the state database, artifact storage, and environment variables.
3. Start the API and any required background services such as schedulers or queue
   workers.
4. Start or serve the frontend shell.
5. Create a session and verify overview, observability, artifact generation, and
   incident triage flows.

## Expected outputs

- A reachable API and frontend shell.
- Healthy control-plane state storage.
- Successful session bootstrap and workspace loading.
- No dependency on removed mock or legacy surfaces.

## Failure modes and troubleshooting

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
