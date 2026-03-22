# History and Trends

## What this page covers

This guide shows how the History screen summarizes repeated validations for a source and
how saved views in the `history` scope make recurring time windows reusable.

## Before you start

- A source with multiple validation runs.
- Permission to read history.
- A clear period and granularity you want to analyze.

## UI path or entry point

Open the history view from a source detail page. History is source-specific, so the
route context remains part of the workflow even when filters are saved.

## Step-by-step workflow

1. Open the history page for the target source.
2. Choose the period and granularity that best match the review window.
3. Review the summary values, trend points, failure frequency, and recent validations.
4. Save the filter combination if the same period and granularity should be reused for
   that source.
5. Compare trend direction with recent incidents and ownership slices if reliability
   has changed.

## Expected outputs

- Trend data that makes pass-rate movement visible over time.
- Failure frequency information tied to recurring validation issues.
- Saved views that can be reused inside the `history` scope for the same source.

## Failure modes and troubleshooting

- If no history appears, confirm that the source has validation runs in the selected
  period.
- If granularity looks too coarse or too dense, switch to a period that matches the run
  volume of the source.
- If saved views seem inconsistent, verify that the view was created in the `history`
  scope and for the intended source context.

## Related APIs

- `GET /sources/{source_id}/history`
- `GET /views`
- `POST /views`
- `PUT /views/{view_id}`

## Next steps

Continue with [Profiling and Comparison](profiling-and-comparison.md) if you want to
compare structure changes with validation trends.
