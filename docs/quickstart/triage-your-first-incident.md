# Triage Your First Incident

## What this page covers

This page introduces the incident workbench: queue routing, assignment, acknowledge
and resolve actions, timeline interpretation, and the relationship between incident
filters and saved views.

## Before you start

- A validation or anomaly event that produced an alert or incident.
- Permission to read and write incidents.
- At least one queue in the workspace, even if it is the default unassigned queue.

## UI path or entry point

Open **Alerts** for the execution workbench or **Notifications Advanced** for queue
configuration and routing behavior. Both screens use the same underlying incident and
queue model.

## Step-by-step workflow

1. Open the Alerts screen and filter to the active queue or assignee.
2. Review severity, status, and correlation information for the incident.
3. Assign the incident to a user or move it to a queue that matches the owning team.
4. Acknowledge the incident when triage begins so operators can distinguish active
   work from new backlog.
5. Resolve the incident once the underlying validation or anomaly condition is handled.
6. Save the filter combination if the same queue or severity slice is used often.

## Expected outputs

- A visible incident timeline with assignment, acknowledgement, and resolution events.
- Queue and assignee filters that affect the workbench in real time.
- Saved view reuse for recurring triage patterns inside the `alerts` scope.

## Failure modes and troubleshooting

- If the alert list is empty when you expect incidents, confirm the workspace,
  severity, and queue filters first.
- If assignment actions fail, verify that the assignee exists and that the queue is
  available in the current workspace.
- If incidents cannot be resolved, inspect required permissions and the incident state
  transition rules.

## Related APIs

- `GET /alerts`
- `POST /alerts/{alert_id}/assign`
- `POST /alerts/{alert_id}/acknowledge`
- `POST /alerts/{alert_id}/resolve`
- `GET /incident-queues`

## Next steps

Continue with the Concepts and Guides sections for deeper coverage of RBAC, ownership,
artifact lifecycle, notification routing, and operational runbooks.
