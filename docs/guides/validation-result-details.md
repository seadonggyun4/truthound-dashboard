# Validation Result Details

## What this page covers

This guide explains how to read a validation result in the dashboard, with special
attention to issues, execution issues, severity, and the bridge from a run to an
artifact or incident workflow.

## Before you start

- A completed validation run.
- Permission to read validations.
- Enough context to know whether the run was expected to pass or fail.

## UI path or entry point

Open a validation detail view from a source or from the source validation list.

## Step-by-step workflow

1. Review the top-line status and run metadata first.
2. Inspect the list of checks and their pass/fail state.
3. Read issues separately from execution issues. Business-rule failures and runtime
   failures should lead to different operator actions.
4. Check issue severity, affected field or column, and any attached unexpected samples.
5. Decide whether the next action is rule tuning, source investigation, artifact
   generation, or incident handling.

## Expected outputs

- A clear distinction between validation failures and execution failures.
- Enough result detail to support operator triage without dropping into raw engine logs.
- A stable bridge to history, artifact generation, and incident creation.

## Failure modes and troubleshooting

- If issue detail seems incomplete, verify the request options that controlled samples
  and unexpected row detail.
- If execution failures dominate the result, move first to source connectivity and
  runtime troubleshooting rather than rule review.
- If severity mapping looks wrong, verify the rule configuration and the validator
  output that produced the issue.

## Related APIs

- `GET /validations/{validation_id}`
- `GET /validations/sources/{source_id}/validations`
- `POST /artifacts/validations/{validation_id}/report`
- `POST /artifacts/validations/{validation_id}/datadocs`

## Next steps

Continue with [History and Trends](history-and-trends.md) or
[Reports and Data Docs](reports-and-datadocs.md).
