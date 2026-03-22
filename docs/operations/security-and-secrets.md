# Security and Secrets

## What this page covers

This page explains the operational security posture of the dashboard around sessions,
permissions, secret storage, and credential rotation.

## Before you start

- Administrative access to the deployment.
- A list of sources or notification channels with secret-bearing fields.
- A clear incident process for suspected credential exposure.

## UI path or entry point

Security work spans the sign-in flow, source detail, notification channel management,
and operations runbooks. There is no single “security page” that replaces these paths.

## Step-by-step workflow

1. Verify session and RBAC behavior in the workspace you operate.
2. Audit which resources contain secret-bearing configuration.
3. Confirm that read paths return redacted configuration only.
4. Rotate source or notification channel credentials when ownership changes or secrets
   are believed to be stale.
5. Review CI secret leak gates before promoting documentation or API changes.

## Expected outputs

- Secret-bearing values stored only in `secret_refs`.
- No raw secrets in API responses, docs examples, or logs.
- Clear permission boundaries for artifact, source, and incident write actions.

## Failure modes and troubleshooting

- If a read path shows raw secret material, treat it as a production issue.
- If rotation appears successful but runtime use fails, inspect the resolved secret and
  the external system state together.
- If permissions look too broad, audit the normalized role-to-permission mappings.

## Related APIs

- `GET /auth/session`
- `GET /permissions`
- `POST /sources/{id}/credentials/rotate`
- `POST /notifications/channels/{id}/credentials/rotate`

## Next steps

Continue with [Reference: Permission Matrix](../reference/permission-matrix.md).
