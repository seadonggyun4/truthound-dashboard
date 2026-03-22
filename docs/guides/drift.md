# Drift

## What this page covers

This guide explains how to compare data states with Truthound drift functionality and
how to interpret drift results in the dashboard without relying on removed monitoring
products.

## Before you start

- A source and comparison target that can both be materialized.
- Permission to run drift comparisons.
- A reasoned baseline for what constitutes meaningful change.

## UI path or entry point

Use the drift comparison flow from the source context or a dedicated drift screen if
your deployment exposes one.

## Step-by-step workflow

1. Select the current source state and the baseline or comparison state.
2. Run the drift comparison.
3. Review the returned summary and drill into affected columns or metrics.
4. Compare the drift signal with profile comparisons and recent validation issues.
5. Decide whether the next action is rule refinement, schema review, or operational
   investigation.

## Expected outputs

- A drift result linked to a source or pair of source states.
- Clear evidence of whether the change is expected, noisy, or operationally important.

## Failure modes and troubleshooting

- If drift results are too broad, validate the comparison target and the time window.
- If the change looks significant but validations did not fail, review whether the
  current rule set is too weak for the new data state.

## Related APIs

- `POST /drift/compare`
- `GET /drift/{comparison_id}`

## Next steps

Continue with [Validation Result Details](validation-result-details.md) or
[History and Trends](history-and-trends.md) to relate drift to run outcomes.
