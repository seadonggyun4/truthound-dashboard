# Artifact Model

Artifacts are the canonical generated outputs of the dashboard. Both downloadable
reports and Data Docs outputs are stored and described through the same artifact model,
which keeps browsing, downloading, filtering, and retention behavior consistent.

Each artifact record links operational context to a generated file or external URL.
Important fields include workspace, source, validation, artifact type, format, status,
title, description, metadata, generation timing, download statistics, locale, theme,
and expiry information. This is enough to support search, retention, auditability, and
workspace-level overview cards without introducing separate report-only storage rules.

There are two first-class artifact types today.

- **report** for operator-facing rendered outputs such as HTML, PDF, or JSON summaries.
- **datadocs** for Truthound-generated documentation bundles or static documentation
  outputs linked to a validation.

The artifact model also clarifies the role of the `/reports` browser route. In the UI,
operators still navigate to `/reports`, but the route is only a label for the artifact
index experience. In the API, the source of truth is always `/artifacts`.

This distinction is important for maintainability. The dashboard no longer needs a
parallel “report history” concept. Any page that wants generated output data can use
artifact records, and any new artifact type can join the same lifecycle without
creating a new top-level storage model. That is why retention, freshness, download
counts, overview slices, and incident runbooks all talk about artifacts rather than
reports alone.
