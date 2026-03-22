# Incident Workbench

The dashboard separates incident configuration from incident execution.

## Pages

- `/notifications/advanced` manages routing rules, throttling, deduplication,
  escalation policies, and queue membership
- `/alerts` is the queue-aware workbench for operators

## Queue-aware operations

- filter incidents by queue, assignee, severity, status, and free-text search
- assign or reassign incidents without leaving the workbench
- acknowledge and resolve incidents with actor identity coming from the active
  dashboard session
- correlate incidents by queue and source to speed up triage

## Data model

- queues live in `incident_queues`
- queue membership lives in `incident_queue_memberships`
- incidents keep `queue_id`, `assignee_user_id`, `assigned_at`, and
  `assigned_by`
- timeline events include assignment and requeue transitions
