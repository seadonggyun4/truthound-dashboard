# Workspaces and Sessions

Workspaces define the operating boundary of Truthound Dashboard. A workspace determines
which sources, teams, domains, queues, saved views, artifacts, and incidents a session
can see. Sessions determine who is acting inside that boundary.

A session is created or restored through the control-plane auth surface. The response
contains the active user, workspace, role, and effective permissions. This is important
because the dashboard does not treat navigation as purely cosmetic; the API enforces
workspace scoping and permission checks on every meaningful action.

The session lifecycle is intentionally simple.

- `GET /auth/session` restores an existing session when possible.
- `POST /auth/session` creates a new local session using the bootstrap or operator
  password.
- `DELETE /auth/session` revokes the session.
- `GET /me` rehydrates the current context without minting a new token.

Workspaces are listed independently so operators can confirm which environment they are
about to change. In single-organization deployments, workspaces are still useful for
separating teams, data environments, or operational regions. The dashboard assumes a
single deployment and organization, but workspace boundaries remain first-class because
they drive permissions, queue routing, saved views, and overview rollups.

Session context also affects UI behavior. When the active role lacks a permission such
as `artifacts:write` or `incidents:write`, the corresponding actions should be hidden
or disabled in the interface. That same restriction applies to API calls, which means
frontend state alone never grants extra capability.

For operators, the practical takeaway is simple: confirm the workspace and role before
creating sources, rotating credentials, or resolving incidents. Almost every “wrong
resource” mistake in a control-plane product starts with an incorrect workspace or a
misread session context.
