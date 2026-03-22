# Run Your First Validation

## What this page covers

This page shows how to execute a validation against a source, read the resulting
`ValidationRunResult`-backed object in the dashboard, and understand where rules,
issues, and execution failures are surfaced.

## Before you start

- A healthy source with a successful connection test.
- Permission to run validations.
- A clear expectation for whether you want to run a small explicit rule set or let the
  validation flow use the configured suite and source metadata.

## UI path or entry point

Open a source detail page and start a validation from the validation panel or quick
action area. The resulting record is also reachable from the source validation list.

## Step-by-step workflow

1. Start a validation from the source page.
2. Choose a simple validator list or a richer request that includes result detail
   controls such as unexpected row sampling or retry behavior.
3. Submit the validation request and wait for the run to complete.
4. Review the canonical run fields: run identifier, run time, status, checks, issues,
   execution issues, row count, column count, and metadata.
5. Open the issue list to verify severity, affected columns, and any unexpected values
   or row samples included in the result payload.

## Expected outputs

- A new validation record under the source.
- Validation status and pass/fail rollups rendered in the UI.
- Issue details and execution issues clearly separated.
- History data that can later be aggregated by the History page.

## Failure modes and troubleshooting

- If the validation cannot start, verify that the source still resolves to a valid
  input and that your role includes validation execution rights.
- If the run finishes with execution issues, inspect source connectivity, schema
  assumptions, and pushdown or parallel settings before changing rules.
- If no issues appear when you expect failures, confirm which validator set was
  selected and whether the source has a saved schema or learned profile.

## Related APIs

- `POST /validations/sources/{source_id}/validate`
- `GET /validations/{validation_id}`
- `GET /validations/sources/{source_id}/validations`

## Next steps

Continue to [Generate Your First Artifact and Data Docs](generate-your-first-artifact.md)
to convert the validation into operator-facing outputs.
