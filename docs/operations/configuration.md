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
5. Confirm observability settings and any logging or metrics integrations.

## Expected outputs

- Reproducible configuration across environments.
- A deployment where sources, notifications, artifacts, and sessions behave
  consistently.

## Failure modes and troubleshooting

- If configuration changes appear to do nothing, confirm that the affected process was
  restarted and that the active environment matches the expected one.
- If only secret-backed features fail, inspect encryption and storage settings before
  assuming application-level bugs.

## Related APIs

- `GET /auth/session`
- `GET /observability/settings`
- `PUT /observability/settings`

## Next steps

Continue with [Security and Secrets](security-and-secrets.md).
