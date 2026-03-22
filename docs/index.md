# Truthound Dashboard

Truthound Dashboard is the operational control-plane for Truthound 3.0. It gives
operators one place to onboard data sources, run and review validations, manage
artifacts and Data Docs, route incidents, control permissions, rotate secrets, and
observe the health of a deployment without re-implementing Truthound validation
semantics inside the dashboard itself.

The product follows a thin data-plane and strong control-plane model.

- Truthound core owns validation execution, profiling, drift comparison, privacy
  operations, checkpoint logic, lineage, reporting, and plugin runtime behavior.
- Truthound Dashboard owns workspaces, sessions, RBAC, source onboarding,
  ownership, incident queues, saved views, secret management, artifacts, and
  operational observability.
- The browser route `/reports` exists as a user-facing route alias for the artifact
  index. All reporting REST contracts are canonical through `/artifacts`.

## Documentation map

This documentation set is organized for operators, platform administrators, and
engineers who need product-level guidance instead of isolated API snippets.

- **Quickstart** walks through the first session, source, validation, artifact, and
  incident workflow.
- **Concepts** explains the object model that connects workspaces, permissions,
  ownership, secrets, artifacts, and incidents.
- **Guides** documents everyday workflows such as source onboarding, validation
  triage, reports and Data Docs generation, queue operations, and observability.
- **Operations** covers deployment, configuration, migrations, quality gates, and
  troubleshooting.
- **API Reference** documents canonical request and response contracts for the
  active REST surface.
- **Reference** provides matrices for source support, permissions, artifact
  capabilities, environment variables, and CLI tasks.
- **Migration** explains the operational reset to the Truthound 3.0 product model.

## Product guarantees

The dashboard documentation treats the following contracts as the source of truth.

- Artifact REST endpoints are `/artifacts`, `/artifacts/capabilities`,
  `/artifacts/{id}`, `/artifacts/{id}/download`, and the generation endpoints for
  report and Data Docs artifacts.
- Secret-bearing configuration is persisted through `secret_refs`. Raw secret values
  are accepted only on create or rotate flows and are never returned by read APIs.
- Saved views are supported for `sources`, `alerts`, `artifacts`, and `history` only.
- Permissions resolve through normalized permissions and role bindings, not legacy
  inline role JSON.
- Removed products such as catalog, collaboration, watcher-style schema monitoring,
  mock surfaces, and legacy `/reports/*` REST APIs are intentionally absent.

## Recommended reading order

If you are new to the product, follow the Quickstart from install through incident
triage. If you are operating an existing deployment, read the architecture,
RBAC, secrets, ownership, incident model, and CI/quality gate sections before
customizing workflows. If you are integrating clients or automation, use the API
reference and the reference matrices together so you can keep UI terminology,
permissions, and REST contracts aligned.
