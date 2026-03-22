# Realtime

## What this page covers

This guide explains the realtime surfaces exposed by the dashboard and how operators
should use them alongside validation history and incident triage.

## Before you start

- Permission to access realtime or websocket-backed features.
- A use case that benefits from streaming state rather than periodic review.

## UI path or entry point

Open the realtime pages or widgets that subscribe to websocket or streaming updates.

## Step-by-step workflow

1. Confirm that realtime connectivity is healthy.
2. Watch the live status surface while triggering or observing a validation-related
   event.
3. Compare realtime updates with the persisted history or incident surfaces to confirm
   that the event also landed in durable state.

## Expected outputs

- Live updates for supported operational surfaces.
- A consistent handoff from transient updates to durable history or incident records.

## Failure modes and troubleshooting

- If live updates stop, check websocket status and session validity.
- If realtime shows an event that never appears in persisted state, inspect the
  underlying event pipeline.

## Related APIs

- `GET /ws/*`
- Event-driven realtime endpoints exposed by the active shell

## Next steps

Use realtime together with [Incident Workbench](incident-workbench.md) when you need
fast operator feedback loops.
