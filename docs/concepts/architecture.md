# Architecture

Truthound Dashboard is designed as a control-plane layered on top of Truthound 3.0.
The product boundary is explicit: Truthound core remains the execution engine for data
quality, while the dashboard provides the operational surfaces that make execution
manageable across workspaces, teams, and incident queues.

At the highest level, the system has four layers.

- The **Truthound adapter layer** translates dashboard actions into Truthound calls for
  validation, profiling, drift comparison, privacy tasks, checkpoint execution,
  lineage, and artifact generation.
- The **control-plane persistence layer** stores users, workspaces, normalized
  permissions, secret references, ownership metadata, incident queues, saved views,
  and artifact records.
- The **API layer** exposes canonical REST families such as `/sources`, `/validations`,
  `/artifacts`, `/alerts`, `/incident-queues`, `/notifications`, and the control-plane
  routes for sessions, roles, permissions, teams, domains, and saved views.
- The **frontend shell** presents operational workflows without embedding its own data
  quality engine. The `/reports` browser route is only a UI alias for the artifact
  index.

The architecture deliberately avoids dashboard-native validation semantics. This keeps
Truthound 3.0 as the only place where check planning, issue generation, Data Docs
rendering, and runtime execution rules are defined. The dashboard instead focuses on
workflow, state, and coordination: who can act, which workspace is active, how secrets
are stored, who owns a source, which queue should receive an incident, and how outputs
are retained.

The current implementation also uses a compatibility boundary inside the backend. The
historical `core/services.py` import path remains available for callers, but the file
is now a compatibility shim. Actual implementations live under domain modules so that
source, validation, history, privacy, and schedule logic can evolve independently.

The most important architectural guarantees are stable across the product.

- `secret_refs` is the only supported storage model for secret-bearing configuration.
- `artifact_records` is the only canonical persistence model for generated outputs.
- Saved views are intentionally limited to `sources`, `alerts`, `artifacts`, and
  `history`.
- Permissions resolve through normalized permission relations instead of legacy role
  JSON.
