# Lineage

## What this page covers

This guide explains how the dashboard exposes lineage structures and why lineage matters
for operational triage rather than only for documentation.

## Before you start

- A deployment with lineage data or tracked lineage operations.
- Permission to read lineage structures.
- A question that benefits from upstream or downstream context, such as impact
  analysis for a failing source.

## UI path or entry point

Open the lineage surface from a source, asset, or lineage-specific view depending on
your workflow.

## Step-by-step workflow

1. Locate the node or asset you want to inspect.
2. Review upstream and downstream relationships.
3. Use lineage context to understand blast radius before acknowledging or resolving
   incidents that may affect multiple assets.
4. Update or refresh lineage information if the tracked graph is stale.

## Expected outputs

- A lineage view that makes dependency direction visible.
- Better incident or validation triage because impact can be assessed before action.

## Failure modes and troubleshooting

- If expected nodes are missing, verify the ingestion or tracking path for lineage
  events.
- If lineage looks outdated, confirm that the underlying process is still publishing
  lineage data.

## Related APIs

- `GET /lineage/*`
- `POST /lineage/*`
- `PUT /lineage/*`

## Next steps

Combine lineage with [Incident Workbench](incident-workbench.md) when triage depends on
upstream and downstream impact.
