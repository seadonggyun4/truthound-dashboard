# Source Credentials

## What this page covers

This guide explains how source credentials are stored, displayed, rotated, and used at
runtime without exposing raw secrets through the API or the UI.

## Before you start

- Permission to write sources.
- A source that uses at least one secret-bearing field such as a password, token, or
  private key.
- Access to the replacement secret if you intend to rotate credentials.

## UI path or entry point

Open a source detail page. Source create and update forms accept raw secret values, but
the read path only shows redacted configuration.

## Step-by-step workflow

1. Create or update the source using raw secret values only inside the write flow.
2. Save the source and confirm that the detail page shows redacted placeholders rather
   than the original secret.
3. Use the credential rotation action when only the secret value changes.
4. Re-run a connection test after rotation to confirm the new `secret_refs` entry can
   be resolved.
5. Review audit or troubleshooting output and confirm that no raw secret values appear.

## Expected outputs

- Redacted source configuration on every read path.
- Secret references stored independently from source metadata.
- Successful connection tests after rotation if the replacement credential is valid.

## Failure modes and troubleshooting

- If a secret rotation succeeds but the connection test fails, validate the new secret
  value against the external system first.
- If a read path exposes the original secret, treat that as a product defect and stop
  using the affected response immediately.
- If non-secret fields disappear during update, confirm that the update payload did not
  unintentionally overwrite the stored configuration.

## Related APIs

- `POST /sources`
- `PUT /sources/{id}`
- `POST /sources/{id}/credentials/rotate`
- `GET /sources/{id}`
- `POST /sources/{id}/test`

## Next steps

Continue to [Source Ownership](source-ownership.md) or [Validation Run Model](validation-run-model.md)
depending on whether you are finishing onboarding or starting execution.
