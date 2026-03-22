# CI

The dashboard CI is designed around three gates:

- PR validation for backend, frontend, docs, and static compatibility checks
- nightly smoke coverage for broader Truthound integrations
- docs rebuild triggers for the main Truthound portal

## PR validation

- backend regression and migration coverage under `tests/`
- control-plane hardening checks for RBAC normalization, artifact cutover, and
  queue-aware incidents
- explicit `no-monolith-services` checks to keep `core/services.py` as a shim
  and prevent new direct `core.services` imports or `_services_impl.py` from
  reappearing
- explicit `no-legacy-surface` regression checks for removed report history,
  removed `/reports` REST endpoints, version history, and legacy permission
  reads
- explicit `no-secret-leak` regression checks for source secret redaction and
  `secret_refs`-backed storage, including notification channel credentials
- migration smoke for legacy roles/generated reports/source secrets and
  notification channel secret cutover
- frontend `type-check` and production build
- static regression gates that fail when removed legacy surfaces reappear

## Nightly focus

- dashboard control-plane smoke coverage
- canonical end-to-end flow: login -> source with secret ref -> validation ->
  report artifact -> Data Docs artifact -> queue assignment -> acknowledgement /
  resolution -> overview refresh -> saved view reuse
- artifact generation and Data Docs persistence
- queue-aware incident workflow rollups
- strict MkDocs build

## Docs gate

- docs regression tests keep stale product claims out
- docs regression tests keep `/artifacts` as the only REST reporting surface
- docs regression tests keep saved-view scope documentation aligned to
  `sources`, `alerts`, `artifacts`, and `history`
- MkDocs strict build verifies navigation and page integrity
