# Troubleshooting Overview

## What this page covers

This page gives operators a troubleshooting framework for separating platform issues,
control-plane issues, and Truthound execution issues.

## Before you start

- The affected workspace and user context.
- A concrete symptom such as failed session bootstrap, missing artifacts, or stuck
  incidents.
- Access to logs, observability signals, and CI history where relevant.

## UI path or entry point

Start from the user-visible failure point, then move to observability, related APIs,
and storage checks.

## Step-by-step workflow

1. Identify the failing surface: session, source, validation, artifact, notification,
   or incident.
2. Confirm the current workspace and permissions.
3. Reproduce the problem through the canonical API if possible.
4. Inspect observability and logs.
5. Check whether the failure is rooted in state storage, secret resolution, or
   Truthound execution behavior.

## Expected outputs

- Faster isolation of the failing layer.
- Less confusion between data-quality failures and control-plane failures.

## Failure modes and troubleshooting

- If a symptom spans multiple pages, begin with the canonical API surface that owns the
  resource.
- If the UI and API disagree, prefer the API response as the authoritative contract and
  then inspect frontend rendering.

## Related APIs

- `GET /overview`
- `GET /observability/*`
- Resource-specific canonical endpoints for the failing feature

## Next steps

Use the source-specific or artifact-and-incident troubleshooting pages below.
