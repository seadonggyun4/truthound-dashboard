# Notifications and Triggers

Notifications and triggers are checkpoint-oriented in 3.0.

- Basic notification channels remain available for operational workflows.
- Advanced routing, throttling, escalation, and incident queues map to
  checkpoint subsystems.
- Trigger pages represent checkpoint trigger and monitoring state, not a
  separate dashboard-only automation engine.

## Operational split

- `/notifications/advanced` is the configuration surface for routing rules,
  deduplication, throttling, escalation policies, and queue membership
- `/alerts` is the incident workbench for queue filtering, assignment,
  acknowledgement, and resolution
- escalation incidents are workspace-scoped and assignment-aware

## Channel secrets

- `/notifications/channels` remains the CRUD surface for basic channels
- channel detail responses are secret-safe and return redacted config values
- stored channel credentials are persisted through `secret_refs`, not inline JSON
- `POST /notifications/channels/{id}/credentials/rotate` rotates webhook URLs,
  tokens, API keys, and SMTP passwords without exposing the current value
- test sends and dispatcher delivery materialize secret refs only at runtime
