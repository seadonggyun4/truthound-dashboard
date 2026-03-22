# Troubleshooting Artifacts, Alerts, and Incidents

## What this page covers

This page focuses on the most common operational failures after execution has already
occurred: missing artifacts, broken Data Docs open paths, empty alert backlogs, and
incidents that cannot be acknowledged or resolved.

## Before you start

- The relevant validation, artifact, alert, or incident identifier.
- Access to the workspace where the issue occurred.
- Enough context to know whether the failure is about generation, listing, download,
  or state transition.

## UI path or entry point

Start from the artifact index or alert workbench, then move to the canonical API and
observability surfaces.

## Step-by-step workflow

1. Confirm the artifact or incident exists through its canonical API.
2. Validate workspace and permission context.
3. Inspect artifact file paths, external URLs, queue assignments, and timeline state as
   appropriate.
4. Compare the failing object with overview counts and any recent cleanup or routing
   changes.
5. Retry the specific action only after the object state is understood.

## Expected outputs

- A clear distinction between missing data, stale pointers, and permission failures.
- Faster recovery for common operator-facing failures.

## Failure modes and troubleshooting

- If `/reports` shows nothing but `/artifacts` does, treat the issue as a UI problem.
- If Data Docs artifacts exist but do not open, inspect `external_url` or file storage.
- If incidents cannot change state, verify permission, queue, and assignee context.

## Related APIs

- `GET /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/download`
- `GET /alerts`
- `POST /alerts/{alert_id}/acknowledge`
- `POST /alerts/{alert_id}/resolve`

## Next steps

Return to [Incident Workbench](../guides/incident-workbench.md) or
[Reports and Data Docs](../guides/reports-and-datadocs.md) once the issue is isolated.
