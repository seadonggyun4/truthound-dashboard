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

1. Treat `Tests PR` and `Docs` as the required workflows for pull requests, merge queue,
   and direct pushes to `main`.
2. Let `Tests PR` run a reusable workflow stack: `preflight`, `backend-py311`,
   `backend-py312`, `backend-ratchet`, `frontend-node20`, `frontend-ratchet`, and
   `docs`.
3. Use `preflight` for workflow hygiene rather than product semantics. It runs
   `actionlint`, dependency review on pull requests, and workflow metadata summaries.
4. Use `backend-py311` and `backend-py312` for the full pytest suite exactly once per
   Python version. The Python 3.11 job also uploads `coverage.xml`.
5. Use `frontend-node20` for `npm ci`, route smoke tests with Vitest and React Testing
   Library, `npm run type-check`, and `npm run build`.
6. Use `backend-ratchet` to enforce required `ruff` and `mypy` coverage for the clean
   artifact-and-secrets backend subtree.
7. Use `frontend-ratchet` to enforce required `eslint` coverage for the clean
   artifact-facing frontend subtree while the broader frontend lint debt remains
   advisory.
8. Use the docs workflow for docs regression tests, internal link checks,
   `mkdocs build --strict`, and the post-success docs rebuild hook on `main`.
9. Use `Tests Nightly` for heavier matrices and advisory debt tracking. Nightly expands
   Python to `3.11`, `3.12`, and `3.13`, Node to `20` and `22`, and runs advisory
   `ruff`, `mypy`, `eslint`, security audit, and secret-backed integration smoke.
10. Use `workflow_dispatch` inputs on nightly runs when you need a narrower matrix or
   when you want to explicitly opt into secret-backed notification or source smoke.
11. Keep secret-backed jobs off pull requests. They run only on nightly schedules or
   manual executions in the `ci-secrets` environment.
12. Use release verification and CodeQL as monitoring and release assurance workflows,
    not as branch-protection gates.

## Expected outputs

- A green `Tests PR` run with required jobs for workflow hygiene, backend validation,
  frontend smoke, docs quality, and ratchet enforcement for the clean artifact-focused
  subtree.
- A green `Docs` run that proves the docs tree can build strictly and only triggers the
  main docs rebuild hook after success on `main`.
- Uploaded artifacts for every important failure domain:
  `pytest-junit.xml`, `coverage.xml`, frontend smoke results, docs logs, actionlint
  output, advisory lint logs, and security audit logs.
- A GitHub step summary that includes job results, collected test counts, docs page
  count, uploaded artifact names, and current advisory debt counts for `ruff`, `mypy`,
  and `eslint`.
- Confidence that `/artifacts` remains the canonical reporting REST surface and that
  `core/services.py` remains a compatibility shim rather than a new monolith.
- Confidence that the clean ratchet subtree cannot silently regress while broader
  repository lint and type debt is still being paid down.

## Failure modes and troubleshooting

- If required checks do not report on merge queue entries, confirm that both `Tests PR`
  and `Docs` support `merge_group` and do not use path filters that can leave status
  checks pending forever.
- If docs deploy fires without a green docs build, the workflow contract is broken.
  `deploy-docs-hook` must only run after the reusable docs workflow succeeds on pushes
  to `main`.
- If secret-backed jobs appear on pull requests, treat that as a security regression.
  The repository contract keeps these jobs on nightly or manual runs only.
- If a PR fails with only artifacts available, inspect uploaded JUnit XML, coverage
  output, frontend Vitest logs, and `mkdocs` logs before rerunning the workflow.
- If the advisory lint/type debt gets larger, use the debt counts from the workflow
  summary to decide whether the change should be deferred, split, or accompanied by
  cleanup work.
- If a ratchet job fails, fix the targeted subtree rather than weakening the manifest.
  Promote new files into the ratchet only after they are stably green.
- If no-legacy or no-monolith gates fail, remove the reintroduced surface instead of
  documenting it or hiding it behind compatibility code.

## Related APIs

- `GET /artifacts`
- `GET /alerts`
- `GET /overview`
- `POST /notifications/channels/{id}/credentials/rotate`

## Next steps

Continue with [Security and Secrets](security-and-secrets.md) and
[State Storage and Migrations](state-storage-and-migrations.md).

## Required gates

- `Tests PR / preflight`
- `Tests PR / backend-py311`
- `Tests PR / backend-py312`
- `Tests PR / backend-ratchet`
- `Tests PR / frontend-node20`
- `Tests PR / frontend-ratchet`
- `Tests PR / docs`
- `Docs / docs`

## Advisory debt gates

Nightly tracks advisory quality debt without blocking pull requests.

- `backend-advisory-quality`
  This job runs full `ruff` and full `mypy src`.
- `frontend-advisory-quality`
  This job runs full `npm run lint`.
- `security-audit`
  This job runs `pip-audit` and `npm audit --omit=dev --audit-level=high`.

## Ratchet phases

- Phase A
  Required checks stay focused on tests, builds, docs, and workflow hygiene.
- Phase B
  Active now. The dashboard enforces a required clean subtree for artifact and secret
  core modules plus artifact-facing frontend pages and hooks.
- Phase C
  Once debt is sufficiently reduced, full-repository `ruff`, `eslint`, and widened
  `mypy` coverage can graduate into required checks.

## Required ratchet subtree

### Backend ratchet

These paths are enforced with required `ruff` and `mypy` checks:

- `src/truthound_dashboard/core/secrets.py`
- `src/truthound_dashboard/core/artifacts.py`
- `src/truthound_dashboard/core/notifications/serialization.py`
- `src/truthound_dashboard/api/artifacts.py`

The source of truth for this list lives in:

- `.github/ci/backend-ruff-ratchet.txt`
- `.github/ci/backend-mypy-ratchet.txt`

### Frontend ratchet

These paths are enforced with required `eslint` checks:

- `frontend/src/api/modules/artifacts.ts`
- `frontend/src/hooks/useArtifacts.ts`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Reports.tsx`
- `frontend/src/pages/Alerts.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/test/app-routes.smoke.test.tsx`

The source of truth for this list lives in:

- `.github/ci/frontend-eslint-ratchet.txt`

## Monitoring workflows

- `CodeQL`
  Runs on `main`, on a weekly schedule, and manually for platform-level security
  monitoring across Python and JavaScript/TypeScript.
- `Release Verification`
  Builds wheel and sdist artifacts, installs the wheel in a fresh environment, runs the
  CLI smoke check, builds the frontend, and validates docs strictly.
- `Dependabot`
  Opens weekly update pull requests for Python dependencies, frontend dependencies, and
  GitHub Actions.
