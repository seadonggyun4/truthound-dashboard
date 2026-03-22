# State Storage and Migrations

## What this page covers

This page explains how the dashboard persists control-plane state, why migration
discipline matters, and what operators should validate after schema changes.

## Before you start

- Access to the state database.
- Awareness of the current release version and migration set.
- A backup or rollback plan appropriate for your environment.

## UI path or entry point

This workflow is backend-facing. The UI only reflects its success through healthy
sessions, visible control-plane objects, and working artifact or incident flows.

## Step-by-step workflow

1. Review the target release and expected schema changes.
2. Apply migrations in order and confirm the schema migration registry is up to date.
3. Validate preserved entities such as workspaces, users, permissions, sources,
   artifacts, and incidents.
4. Confirm deleted or legacy tables are no longer needed by active code paths.
5. Run smoke validation for session bootstrap, source reads, artifact listing, queue
   reads, and notification channel access.

## Expected outputs

- A schema that matches the active codebase.
- Preserved control-plane entities available after migration.
- No active dependency on removed legacy storage models.

## Failure modes and troubleshooting

- If the application starts but key pages fail, inspect whether a migration partially
  applied or whether preserved entities were not backfilled correctly.
- If notification or source secrets fail after migration, validate the `secret_refs`
  backfill path before rotating everything manually.

## Related APIs

- `GET /auth/session`
- `GET /sources`
- `GET /artifacts`
- `GET /alerts`

## Next steps

Continue with [Troubleshooting Overview](troubleshooting-overview.md).
