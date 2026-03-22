# Secrets and Credential Rotation

Truthound Dashboard separates secret-bearing configuration from readable operational
state. The readable objects, such as sources and notification channels, keep structured
configuration with redacted secret placeholders. The secret material itself is stored
in `secret_refs`.

This model has a few practical consequences.

- Raw secret values are accepted only when you create a resource or explicitly rotate a
  credential.
- Read APIs never return the original secret value.
- Runtime execution resolves the reference only when the source or channel is about to
  be used.
- Audit and error payloads must redact secret-bearing fields before serialization.

The same pattern applies to both source credentials and notification channel
credentials. A source config might contain a password or token reference. A
notification channel config might contain a webhook URL, SMTP password, API key, or bot
token reference. In both cases the dashboard persists a reference payload and returns a
redacted configuration to the UI.

Rotation is a first-class operation because operators often need to update credentials
without rewriting the rest of the configuration. The product therefore supports create,
update, and rotate paths separately. Non-secret fields can usually be edited inline,
while secret-bearing fields are rotated with dedicated flows. This makes it easier to
avoid accidental secret leaks in logs, screenshots, or copied API responses.

When you troubleshoot authentication or delivery issues, focus on whether a resource
can successfully materialize its secret references at runtime. A stored resource with a
valid shape can still fail if the encrypted value is stale, deleted, or mismatched to
the target system.
