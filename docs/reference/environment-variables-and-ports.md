# Environment Variables and Ports

This reference lists the categories of runtime settings operators should expect when
deploying the dashboard.

| Category | Purpose |
| --- | --- |
| Database settings | Connect the control-plane state database |
| Session bootstrap settings | Configure local session creation |
| Encryption and secret settings | Support `secret_refs` storage and rotation |
| Artifact storage settings | Control artifact file paths or backing stores |
| Frontend or API bind settings | Expose the shell and API on the correct interfaces |
| Observability settings | Configure metrics, logs, and status reporting |

Operational guidance:

- Keep environment-specific values outside the repository.
- Rotate secret-related values with the same discipline used for source and
  notification credentials.
- Re-verify startup and session bootstrap after changing bind or storage settings.
