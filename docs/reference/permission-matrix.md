# Permission Matrix

This matrix summarizes the control-plane model. Exact role composition may vary by
deployment, but the permission keys remain the canonical contract.

| Permission family | Typical actions |
| --- | --- |
| `sources:read` / `sources:write` | List, create, update, test, rotate credentials, delete sources |
| `artifacts:read` / `artifacts:write` | Browse, download, generate, delete, clean up artifacts |
| `incidents:read` / `incidents:write` | Read alerts, assign, acknowledge, resolve incidents |
| `notifications:read` / `notifications:write` | Manage channels, rules, tests, credential rotation |
| `roles:read` / `permissions:read` | Inspect RBAC configuration |
| `users:read` | Read operator lists for ownership and assignment |

Guidance:

- Roles are just bundles. Permissions are the source of truth.
- Ownership does not grant permission by itself.
- Session payloads expose the effective permission set for the active workspace.
