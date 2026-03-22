# Architecture

Truthound Dashboard 3.0 is a thin operational layer over Truthound 3.0 with a
stronger control-plane for day-to-day operations.

## Principles

- Root API first: `truthound.check`, `profile`, `scan`, `mask`, `learn`
- Namespace features only when they exist upstream:
  `truthound.checkpoint`, `datadocs`, `drift`, `lineage`, `ml`,
  `observability`, `plugins`, `profiler`, `realtime`, `stores`
- No dashboard-only validation semantics
- Preserve the established dashboard UI and Intlayer application i18n
- Keep Truthound-owned execution in adapter boundaries and reserve dashboard
  persistence for control-plane concerns

## Runtime shape

- Backend: FastAPI plus bounded contexts for authz/RBAC, sources, incidents,
  artifacts, overview, and Truthound adapters
- Domain services: `core/services.py` is a compatibility shim only; concrete
  source/validation/schema/profile/history/drift/schedule/privacy services live
  directly in `core/domains/*.py`
- Frontend: existing React layout and patterns, trimmed to the Truthound 3.0 surface
- Contracts: canonical Truthound 3.0 payloads, especially `ValidationRunResult`
- RBAC: normalized `permissions` and `role_permissions` with effective
  permission resolution from `membership -> role -> permissions`
- Secrets: canonical `secret_refs` with DB-backed encrypted storage behind the
  `SecretProvider` seam
- Ownership: normalized `teams`, `domains`, and `source_ownerships` so the
  overview, filters, and incident routing operate on the same control-plane
  model
- Artifacts: canonical `artifact_records` for reports and Data Docs
- Incidents: queue-aware workbench with assignment, acknowledgement, resolution,
  and saved-view support
- Docs: MkDocs in this repo, mirrored into the main Truthound docs portal
