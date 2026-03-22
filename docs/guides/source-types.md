# Source Types

## What this page covers

This guide explains how source types are exposed in the dashboard, how operators should
evaluate them, and how source type choice affects connection testing, profiling, and
validation.

## Before you start

- Permission to read sources.
- A target system or dataset you want to connect.
- A basic understanding of whether the workload is file-based, dataframe-based, SQL,
  or another supported Truthound adapter surface.

## UI path or entry point

Use the source creation form or the source type list supplied to the UI during the
create workflow.

## Step-by-step workflow

1. Inspect the supported source types before creating a source.
2. Match the type to the system you actually operate rather than forcing a generic
   type that hides connection semantics.
3. Review the required fields for that type, especially secret-bearing fields.
4. Validate the type with a connection test after creation.
5. Use the same source type assumptions when configuring profiling, validation, and
   drift workflows later.

## Expected outputs

- A clear source type selection with a matching configuration shape.
- A source definition that can be materialized into a Truthound data input without
  custom dashboard-only adapters.

## Failure modes and troubleshooting

- If the type appears to fit but the config shape does not, inspect the channel or
  source schema metadata rather than guessing field names.
- If a type is not listed, treat that as an unsupported dashboard surface rather than
  trying to revive removed legacy integrations.

## Related APIs

- `GET /sources/types`
- `POST /sources`
- `POST /sources/{id}/test`

## Next steps

Read [Source Onboarding](source-onboarding.md) for the full create flow and
[Source Credentials](source-credentials.md) for secret-handling details.
