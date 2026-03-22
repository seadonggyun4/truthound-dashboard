# Source Support Matrix

Truthound Dashboard documents source types as control-plane inputs rather than as a
separate execution engine. Use this matrix to decide which onboarding workflow and
credential pattern to expect.

| Category | Typical examples | Secret handling | Common next step |
| --- | --- | --- | --- |
| File-backed | CSV, parquet, JSON, local files | Usually none or path-level only | Profile, validate |
| SQL-backed | Warehouse or database connections | Passwords, tokens, keys in `secret_refs` | Test connection, validate |
| Runtime dataframe | Pandas or Polars-backed inputs | Rare | Profile, compare |
| Distributed execution | Spark-style or remote compute | Tokens, host details | Test, profile, validate |

Operational notes:

- Always choose the most specific type available rather than a generic fallback.
- If a source requires credentials, use create or rotate flows instead of expecting the
  API to return the stored secret later.
- Ownership assignment is independent of source type.
