# Schema Evolution

## What this page covers

This guide explains how to review schema evolution in the dashboard using learned schema
or profile comparisons instead of the removed watcher-style products from earlier
dashboard iterations.

## Before you start

- A source with learned schema or profile snapshots.
- Permission to read schema-related surfaces.
- A clear baseline snapshot for comparison.

## UI path or entry point

Open the schema evolution surface from the source or schema context.

## Step-by-step workflow

1. Select the current and baseline schema or profile snapshots.
2. Review additions, removals, and changed field characteristics.
3. Compare the schema deltas with recent validation failures and drift findings.
4. Decide whether to update rules, profile expectations, or downstream operational
   ownership.

## Expected outputs

- A focused view of structural change without relying on removed watcher products.
- Better context for deciding whether a change is harmless, expected, or incident-worthy.

## Failure modes and troubleshooting

- If schema deltas are missing, confirm that snapshots were learned and stored.
- If changes appear but no validations fail, inspect whether the rule set lags behind
  the current structure.

## Related APIs

- `GET /schema-evolution/*`
- `GET /schemas/*`
- `POST /schemas/*`

## Next steps

Continue with [Drift](drift.md) or [Rule Management](rule-management.md).
