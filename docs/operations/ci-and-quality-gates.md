# CI and Quality Gates

## What this page covers

This page describes the operational quality gates that keep the dashboard aligned with
its 3.0 control-plane model, including docs quality, legacy surface regression checks,
secret leak protection, and artifact-centric end-to-end verification.

## Before you start

- Access to the CI workflows.
- A deployment or branch where you can run backend, frontend, and docs checks.
- Familiarity with the artifact-only reporting surface and the current saved-view
  scope.

## UI path or entry point

This is an operations and repository workflow rather than a UI-first workflow. The UI
only reflects the results indirectly through product behavior.

## Step-by-step workflow

1. Run backend tests and frontend type-check and build gates.
2. Run docs regression tests and `mkdocs build --strict`.
3. Verify the no-legacy surface gate so removed APIs and legacy products do not return.
4. Verify the no-secret-leak gate so response payloads and docs examples never expose
   raw credentials.
5. Run migration smoke and canonical end-to-end flows, especially artifact generation,
   Data Docs generation, queue assignment, acknowledgement, and resolution.

## Expected outputs

- A green CI run with no legacy, no secret leaks, and strict docs validation.
- Confidence that `/artifacts` remains the canonical reporting REST surface.
- Confidence that `core/services.py` remains a compatibility shim rather than a new
  monolith.

## Failure modes and troubleshooting

- If docs pass but product behavior regresses, inspect canonical end-to-end coverage.
- If secret leak gates fail, treat the issue as high priority and stop publishing docs
  or API changes until the leak is fixed.
- If no-legacy gates fail, remove the reintroduced surface instead of documenting it.

## Related APIs

- `GET /artifacts`
- `GET /alerts`
- `GET /overview`

## Next steps

Continue with [Security and Secrets](security-and-secrets.md) and
[State Storage and Migrations](state-storage-and-migrations.md).
