# Profiling and Comparison

## What this page covers

This guide explains how profiling and profile comparison fit into the operator workflow
for onboarding and change analysis.

## Before you start

- A source that can be read successfully.
- Permission to run profile operations.
- A baseline profile or a comparison target if you plan to compare outputs.

## UI path or entry point

Use the profiling surfaces from a source detail page or from dedicated profile actions.

## Step-by-step workflow

1. Generate a profile for the source.
2. Review column-level statistics, null rates, distributions, and low-cardinality
   values.
3. Save or reuse the profile as a baseline if you expect future comparisons.
4. Run a comparison against another profile when data shape or drift is under review.
5. Use the results to refine rules or explain changes in incident frequency.

## Expected outputs

- A usable profile artifact for the source.
- Structured comparisons that highlight differences in the measured profile values.
- A direct bridge to rule suggestion and schema or drift analysis.

## Failure modes and troubleshooting

- If the profile cannot be generated, confirm that the source can be materialized and
  that profiling is supported for that source type.
- If comparisons are noisy, reduce the number of changing inputs before drawing
  conclusions about stability.

## Related APIs

- `POST /profile/sources/{source_id}`
- `POST /profile/comparisons`
- `GET /profile/{profile_id}`
- `GET /profile/comparisons/{comparison_id}`

## Next steps

Continue with [Rule Suggestions](rule-suggestions.md) or [Drift](drift.md).
