# RBAC and Permissions

Truthound Dashboard uses normalized RBAC instead of ad hoc role payloads. Roles still
exist as user-facing concepts, but the source of truth for authorization is the
permission registry and the role-to-permission mapping.

The model is intentionally simple.

- **Permissions** define granular actions such as reading sources, writing artifacts,
  or managing incidents.
- **Roles** group those permissions into reusable operator profiles.
- **Memberships** connect a user to a role inside a workspace.
- **Sessions** materialize the effective permission set for the active user and
  workspace.

This matters operationally because documentation, UI affordances, and API guards can
all point to the same permission keys. When you grant or remove access, you update the
role-to-permission mapping rather than editing legacy inline JSON blobs. The API
surface also reflects this design: roles can be listed, but the canonical metadata for
authorization comes from the permissions endpoint and the resolved permission list
returned with the active session.

Permission boundaries align with product surfaces. Sources, artifacts, incidents,
queues, notifications, and control-plane administration all have their own read/write
scopes. This makes it possible to give an operator broad incident access without also
granting permission to rotate source credentials or delete artifacts.

RBAC also interacts with saved views and overview slices. Users can save filters only
within scopes they can read, and overview cards only summarize objects inside the
current workspace that the session is allowed to query. When documentation refers to a
feature such as incident assignment or artifact deletion, it should be read together
with the permission matrix rather than as an unconditional capability.
