# Core Object Model

Truthound Dashboard becomes easier to operate when you think in terms of a small set of
connected objects instead of isolated pages. The core model ties workspace identity,
data assets, operational outputs, and incident routing together.

The primary objects are:

- **Workspace**: the top-level operational boundary for sources, queues, saved views,
  permissions, and overview slices.
- **User, role, and permission**: the identity graph that controls who can read or
  mutate a resource inside a workspace.
- **Source**: a configured data input with non-secret settings, secret references,
  optional ownership assignments, and lifecycle metadata.
- **Validation**: a source-bound execution record derived from Truthound 3.0 run
  semantics.
- **Artifact**: a generated output linked to a validation, such as a downloadable
  report or Data Docs bundle.
- **Incident**: an operational object used for triage, assignment, acknowledgement,
  resolution, and correlation across validation or anomaly signals.
- **Queue**: a workspace-scoped routing object that groups incidents and defines an
  operational inbox for teams or users.
- **Saved view**: a reusable filter payload for `sources`, `alerts`, `artifacts`, or
  `history`.

These objects are connected by explicit foreign keys and scope rules. A source belongs
to one workspace. A validation belongs to one source. An artifact can point to both
the source and the validation that produced it. An incident belongs to one workspace
and may also point to a queue or assignee. Saved views are always workspace-scoped and
cannot cross scopes.

Ownership enriches, rather than replaces, this model. An owner user, team, or domain
can be attached to a source so that overview slices and incident triage align with
organizational boundaries. Secrets also fit into the same graph: the source or
notification channel stores a reference payload, while the actual encrypted value lives
inside `secret_refs`.

This object model is what keeps the dashboard extensible. New UI flows tend to combine
existing objects rather than inventing new private models, which keeps the product
easier to document and maintain.
