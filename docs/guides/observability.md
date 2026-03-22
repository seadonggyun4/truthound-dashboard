# Observability

## What this page covers

This guide explains how the dashboard exposes observability settings, metrics, and
status surfaces for operators who need to verify the health of the control-plane.

## Before you start

- Permission to read observability or platform settings.
- A reason to inspect runtime health, metrics, or logging behavior.

## UI path or entry point

Open the Observability page or the platform status surfaces from the shell.

## Step-by-step workflow

1. Review the current observability configuration.
2. Inspect dashboard health signals and metric summaries.
3. Compare operational failures with quality gates such as no-legacy or no-secret-leak
   checks if the issue is discovered during CI.
4. Update the relevant configuration only if your deployment policy allows it.

## Expected outputs

- Clear status indicators for the control-plane.
- Enough context to distinguish runtime issues from data quality issues.

## Failure modes and troubleshooting

- If metrics are missing, validate the configured backend or exporter first.
- If observability is healthy but incidents keep accumulating, investigate queue
  operations and validation failures instead of the platform itself.

## Related APIs

- `GET /observability/*`
- `PUT /observability/settings`

## Next steps

Continue with [CI and Quality Gates](../operations/ci-and-quality-gates.md).
