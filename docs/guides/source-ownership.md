# Source Ownership

## What this page covers

This guide explains how to assign and maintain source ownership so that overview slices,
incident routing, and saved views reflect real operational responsibility.

## Before you start

- Permission to read and write sources.
- Existing users, teams, and domains in the workspace.
- Agreement on whether unowned sources are allowed in your operating model.

## UI path or entry point

Ownership is configured from the source create or source detail flow. Supporting team
and domain definitions are created through the control-plane APIs.

## Step-by-step workflow

1. Decide whether the source should remain unowned or be assigned to a specific owner,
   team, and domain.
2. Create missing teams or domains before editing the source if needed.
3. Apply ownership updates on the source detail page.
4. Revisit the Dashboard overview to confirm that the source appears in the expected
   owner, team, and domain slices.
5. Use ownership filters in the Sources screen when triaging responsibility at scale.

## Expected outputs

- Owner, team, and domain metadata attached to the source.
- Correct representation in `sources by owner`, `sources by team`, and
  `sources by domain` overview slices.
- A visible unowned state for sources without assignments.

## Failure modes and troubleshooting

- If the source does not appear in ownership slices, verify that the ownership update
  was saved in the current workspace.
- If ownership appears correct but incidents are still routed poorly, inspect queue and
  notification configuration separately because ownership does not replace routing.

## Related APIs

- `GET /teams`
- `POST /teams`
- `GET /domains`
- `POST /domains`
- `GET /sources/{id}/ownership`
- `PUT /sources/{id}/ownership`

## Next steps

Read [History and Trends](history-and-trends.md) and [Incident Workbench](incident-workbench.md)
to see how ownership shows up in ongoing operations.
