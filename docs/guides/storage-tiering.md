# Storage Tiering

## What this page covers

This guide explains how storage tiers, policies, and migration records are exposed in
the dashboard for operators who manage retention or movement of persisted assets.

## Before you start

- Permission to read or manage tiering.
- A target storage policy or migration scenario.

## UI path or entry point

Open the storage or tiering surfaces from the shell navigation.

## Step-by-step workflow

1. Review existing storage tiers.
2. Inspect or create policies that map conditions to migration behavior.
3. Review tiering configs and migration history before running or forcing changes.
4. Execute or monitor policy runs with care, especially in production environments.

## Expected outputs

- Visible storage tiers and policy definitions.
- Migration history that supports audit and operational review.

## Failure modes and troubleshooting

- If a migration does not run, inspect policy applicability and item state first.
- If access latency or missing artifacts appears after migration, verify the target
  tier and policy outcome before retrying downloads.

## Related APIs

- `GET /tiers`
- `GET /policies`
- `GET /configs`
- `GET /migrations`

## Next steps

Continue with [State Storage and Migrations](../operations/state-storage-and-migrations.md).
