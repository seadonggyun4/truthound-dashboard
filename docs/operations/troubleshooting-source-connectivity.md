# Troubleshooting Source Connectivity

## What this page covers

This page focuses on one of the most common operational problems: a source that saves
correctly but cannot be tested, profiled, or validated successfully.

## Before you start

- The source identifier.
- Access to the current source configuration and ownership context.
- The replacement secret if credential rotation may be required.

## UI path or entry point

Start from the source detail page and the source connection test action.

## Step-by-step workflow

1. Confirm the source type and non-secret configuration.
2. Re-run the connection test.
3. If the connection test fails, review secret rotation history and revalidate the
   current credentials with the external system.
4. Inspect whether the failure is type-specific, environment-specific, or scoped to one
   workspace.
5. Retry the downstream operation only after the connection test succeeds.

## Expected outputs

- A clear answer to whether the source can be materialized.
- A documented path to either fix configuration, rotate credentials, or escalate the
  issue outside the dashboard.

## Failure modes and troubleshooting

- If create works but test fails, check the runtime materialization path and the
  resolved secret value.
- If test succeeds but validation fails, the problem may be schema, rule, or engine
  related rather than connectivity related.

## Related APIs

- `GET /sources/{id}`
- `POST /sources/{id}/test`
- `POST /sources/{id}/credentials/rotate`
- `POST /validations/sources/{source_id}/validate`

## Next steps

Continue with [Validation Run Model](../guides/validation-run-model.md).
