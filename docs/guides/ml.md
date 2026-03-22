# ML

## What this page covers

This guide describes the dashboard surfaces that expose Truthound ML-adjacent features
such as anomaly analysis, rule learning, and related operational review.

## Before you start

- Permission to access ML or anomaly features.
- A source or dataset state where learned or anomalous behavior matters.

## UI path or entry point

Use the anomaly or ML surfaces available in the dashboard shell.

## Step-by-step workflow

1. Review the available ML-oriented workflows for your source or artifact.
2. Run or inspect anomaly results.
3. Compare the results with validation issues, history, and ownership slices before
   escalating them into incident work.

## Expected outputs

- A product surface that exposes supported Truthound ML functionality without inventing
  a separate dashboard-native monitoring engine.

## Failure modes and troubleshooting

- If anomaly output is noisy, compare it with profile and validation history before
  changing operational thresholds.
- If the ML surface is unavailable for a source, confirm that the underlying Truthound
  feature applies to the current data type.

## Related APIs

- `GET /anomaly/*`
- `POST /anomaly/*`

## Next steps

Continue with [Incident Workbench](incident-workbench.md) if anomaly findings need
queue-based triage.
