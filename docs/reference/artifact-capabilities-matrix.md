# Artifact Capabilities Matrix

Use this matrix together with `GET /artifacts/capabilities` to understand the supported
artifact surface.

| Capability | Meaning |
| --- | --- |
| `artifact_type=report` | Rendered operator-facing report output |
| `artifact_type=datadocs` | Truthound-generated Data Docs output |
| `formats` | Supported report output formats |
| `themes` | Presentation themes for rendered outputs |
| `locales` | Supported localized report output codes |
| `download_url` | Canonical path for artifact download or open flow |
| `external_url` | Direct open path when the artifact resolves outside local file storage |

Guidance:

- Use `/artifacts/capabilities` before building custom UI logic around generation.
- Treat `/reports` as a browser route only, never as the REST contract.
