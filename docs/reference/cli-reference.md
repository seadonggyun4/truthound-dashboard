# CLI Reference

The dashboard CLI is intentionally small and operationally focused.

| Command family | Purpose |
| --- | --- |
| `truthound-dashboard` runtime commands | Start the application stack or supporting processes |
| `truthound translate` | Use the Intlayer-oriented translation pipeline and provider-backed AI translation flow |
| Verification helpers | Run product verification, docs builds, or repository checks depending on your environment |

Guidance:

- Prefer the CLI for startup and translation workflows.
- Use CI gates for regression detection instead of relying only on local smoke tests.
- The translation pipeline remains part of the product surface even though the docs are
  maintained in English as the canonical language.
