# Incident and Queue Model

Incidents are the operational objects that turn validation failures, anomaly signals,
and escalation policies into work. Queues are the inboxes that organize that work
inside a workspace.

The model supports a predictable operator workflow.

- An incident is created or surfaced from a validation or anomaly event.
- The incident enters a queue, usually the default unassigned queue if nothing more
  specific is configured.
- A user can be assigned to the incident directly.
- Operators acknowledge the incident when triage begins.
- Operators resolve the incident when the condition has been addressed.

Each incident keeps a timeline so that assignment, acknowledgement, requeue, and
resolution events remain auditable. This is important in a multi-operator environment
because it distinguishes backlog from active work and shows how escalation policies
interacted with human handling.

Queues are workspace-scoped. Membership management determines who should be offered as
default operators for a queue, but assignment can still be more specific than queue
membership when needed. Saved views in the `alerts` scope make recurring queue slices
reusable, for example “High severity incidents for the Platform queue” or “My open
incidents”.

The incident and queue model is intentionally separate from notification channel
configuration. Notification rules decide where messages go. Incident queues decide
where work lands. Keeping those concerns separate makes escalation paths easier to
document and troubleshoot.
