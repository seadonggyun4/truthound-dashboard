# Saved View Scope Matrix

Saved views are intentionally limited. The supported scopes are documented here so that
runbooks, UI copy, and automation all stay aligned.

| Scope | Supported screen | Typical filters |
| --- | --- | --- |
| `sources` | Sources list | `search`, `status`, `owner_user_id`, `team_id`, `domain_id` |
| `alerts` | Alerts workbench | `search`, `status`, `severity`, `queue_id`, `assignee_user_id` |
| `artifacts` | `/reports` artifact index | `search`, `status`, `artifact_type`, `format` |
| `history` | Source history | `period`, `granularity`, source-specific context |

Not supported:

- Global validations list saved views
- Removed version history surfaces
- Legacy report-history scopes
