# Enterprise Sampling

## What this page covers

This guide explains how enterprise sampling features are surfaced in the dashboard for
operators who need bounded data review at scale without moving full datasets through
interactive workflows.

## Before you start

- Permission to access enterprise sampling features.
- A source where full reads are too expensive or operationally risky.
- A clear understanding of why a sampled workflow is acceptable for the task.

## UI path or entry point

Open the enterprise sampling surface from the source or advanced workflow area exposed
by your deployment.

## Step-by-step workflow

1. Choose the source and sampling strategy.
2. Review the resulting sampled output and its metadata.
3. Use the sample for inspection, profiling support, or troubleshooting, but avoid
   treating it as a perfect substitute for the full dataset.
4. Compare the sample with recent validation and drift outcomes before making broad
   operational decisions.

## Expected outputs

- A bounded sample that is easier to inspect or share operationally.
- Clear metadata about the sampling mode and limits used.

## Failure modes and troubleshooting

- If the sample is too small or unrepresentative, adjust the sampling strategy rather
  than drawing conclusions from an obviously poor sample.
- If enterprise sampling is unavailable for a source, confirm that the source type and
  deployment support it.

## Related APIs

- `POST /enterprise-sampling/*`
- `GET /enterprise-sampling/*`

## Next steps

Continue with [Profiling and Comparison](profiling-and-comparison.md) or
[Reports and Data Docs](reports-and-datadocs.md).
