# Validations

The Validations module constitutes the primary mechanism for executing data quality checks and inspecting their results. It encompasses the full lifecycle of a validation run -- from configuration and execution through to result analysis, versioning, and historical trend monitoring.

## Overview

Data validation is defined as the process of systematically verifying that a dataset conforms to a prescribed set of quality rules. Truthound Dashboard supports 289+ built-in validators spanning schema integrity, completeness, uniqueness, distribution, string patterns, datetime formats, aggregate statistics, cross-table relationships, geospatial coordinates, drift detection, anomaly detection, and privacy compliance.

The validation system is composed of three interrelated subsystems:

| Subsystem | Purpose | Page |
|-----------|---------|------|
| **Validation Execution Framework** | Run validators against a data source and inspect results | Source Detail |
| **Validation History and Longitudinal Analysis** | Track pass/fail trends over time with statistical analysis | History |
| **Version Management and Snapshot Comparison** | Create and compare snapshots of validation results | Version History |

## Validation Execution Framework

### Running a Validation

Validation is initiated from the Source Detail page. The execution workflow is structured as follows:

1. **Select Validators**: The Validator Selector is employed to designate which validators are to be executed
2. **Configure Parameters**: Validator-specific parameters (thresholds, patterns, column selections) are adjusted as required
3. **Execute**: The validation process is launched by selecting "Configure & Run"
4. **Review Results**: Detected issues are examined, grouped by severity classification

### Validator Configuration

The Validator Selector exposes a comprehensive interface through which validators may be selected and configured:

| Feature | Description |
|---------|-------------|
| **Preset Templates** | Quick-start configurations: All Validators, Quick Check, Schema Only, Data Quality |
| **Category Filtering** | Filter by 14 categories (schema, completeness, uniqueness, distribution, etc.) |
| **Search** | Find validators by name, description, or tag |
| **Parameter Configuration** | Type-specific input forms (text, number, select, boolean, column list) |
| **Severity Override** | Override the default severity level for any validator |
| **Column Autocomplete** | Schema-aware column selection with autocomplete |

### Execution Parameters

The validation engine accommodates several execution-level parameters that govern how validators are applied. Parameters introduced through the Truthound core engine enhancement phases (PHASE 1–5) are denoted accordingly.

| Parameter | Description | Default | Phase |
|-----------|-------------|---------|-------|
| **validators** | List of validators to execute | All enabled | — |
| **validator_config** | Per-validator parameter overrides | None | — |
| **min_severity** | Minimum severity threshold for reporting | low | — |
| **parallel** | Enable parallel execution across validators | false | — |
| **max_workers** | Number of parallel worker threads | CPU count | — |
| **pushdown** | Enable SQL query pushdown for database sources | false | — |
| **schema** | Schema file path or Schema object for constraint validation | Auto-detected | — |
| **auto_schema** | Automatically learn schema before validation | false | — |
| **result_format** | Progressive detail level controlling result enrichment depth | summary | PHASE 1 |
| **include_unexpected_rows** | Include failure row DataFrame in SUMMARY or higher results | false | PHASE 1 |
| **max_unexpected_rows** | Maximum number of failure rows to return (1–10,000) | 1000 | PHASE 1 |
| **catch_exceptions** | Enable exception isolation mode; errors are captured in the report rather than aborting execution | true | PHASE 5 |
| **max_retries** | Maximum retry attempts for transient errors with exponential backoff (0–10) | 3 | PHASE 5 |

#### Result Format System (PHASE 1)

The `result_format` parameter implements a four-level progressive disclosure model that governs the granularity of validation output. This system was introduced to enable practitioners to balance the trade-off between diagnostic richness and computational overhead.

| Level | Description | Enrichment Phases |
|-------|-------------|-------------------|
| **BOOLEAN_ONLY** | Pass/fail determination only; bypasses all enrichment phases | Phase 1 (aggregates) |
| **BASIC** | Adds failure counts and sample values | Phases 1–2 (aggregates + samples) |
| **SUMMARY** | Adds value frequency distributions (default) | Phases 1–3 (aggregates + samples + value counts) |
| **COMPLETE** | Adds full failure row DataFrames and debug queries | Phases 1–4 (all enrichment phases) |

The selection of `result_format` directly influences both the computational cost of validation and the volume of data transmitted through the API response payload. For high-frequency automated validations, `BOOLEAN_ONLY` or `BASIC` are recommended to minimize latency.

#### Exception Isolation and Auto-Retry (PHASE 5)

The exception isolation subsystem provides fault-tolerant validation execution through a multi-tier recovery mechanism:

1. **Exception Capture**: When `catch_exceptions=True`, validator errors are caught and recorded as `ExceptionInfo` objects within the validation report, rather than propagating as unhandled exceptions that would abort the entire validation session.
2. **Automatic Retry**: Transient errors (timeout, connection failure) are automatically retried up to `max_retries` times with exponential backoff. Permanent errors (configuration, data type mismatches) are not retried.
3. **Three-Tier Fallback** (Expression Batch Executor): When a batched expression set fails, the executor falls back to per-validator execution; if that also fails, it falls back to per-expression execution, thereby maximizing the number of successful validations in a single run.
4. **Failure Classification**: Each exception is classified into one of four categories — `transient`, `permanent`, `configuration`, or `data` — enabling targeted remediation.

### Validation Results

Upon completion, the validation result is comprised of the following fields. Fields introduced through the core engine enhancement phases are annotated with their corresponding phase identifiers.

| Field | Description | Phase |
|-------|-------------|-------|
| **passed** | Boolean indicating overall pass/fail status | — |
| **total_issues** | Total number of issues detected | — |
| **has_critical** | Whether any critical-severity issues were found | — |
| **has_high** | Whether any high-severity issues were found | — |
| **issues** | Detailed list of individual issues | — |
| **execution_time** | Duration of the validation run | — |
| **validators_run** | Number of validators that were executed | — |
| **statistics** | Aggregate validation statistics including success rate, issues by severity/column/validator, and most problematic columns | PHASE 2 |
| **validator_execution_summary** | Summary of validator execution states (executed, skipped, failed) with skip reasons | PHASE 4 |
| **exception_summary** | Aggregate exception statistics including retry counts, recovery rates, and circuit breaker trip counts | PHASE 5 |

#### Structured Validation Statistics (PHASE 2)

The `statistics` object provides a comprehensive analytical decomposition of the validation session, enabling multi-dimensional analysis of data quality:

| Statistic | Description |
|-----------|-------------|
| **total_validations** | Total number of individual validator executions |
| **successful_validations** | Number of validators that completed without issues |
| **unsuccessful_validations** | Number of validators that detected quality issues |
| **success_percent** | Percentage of successful validations |
| **issues_by_severity** | Distribution of issues across severity levels |
| **issues_by_column** | Distribution of issues across affected columns |
| **issues_by_validator** | Distribution of issues across validator types |
| **most_problematic_columns** | Ranked list of columns exhibiting the highest issue density |

#### Validator Execution Summary (PHASE 4)

When the Truthound core engine's Directed Acyclic Graph (DAG) execution is active, validators may be conditionally skipped based on dependency relationships. The `validator_execution_summary` provides transparency into this process:

| Field | Description |
|-------|-------------|
| **total_validators** | Total number of validators in the execution plan |
| **executed** | Number of validators that completed execution |
| **skipped** | Number of validators that were bypassed due to dependency failures |
| **failed** | Number of validators that encountered runtime errors |
| **skipped_details** | Per-validator skip reasons (e.g., "Schema validation failed for column X") |

This mechanism ensures that downstream validators are not executed against data that has already been determined to violate prerequisite constraints, thereby reducing spurious issue reports and improving the signal-to-noise ratio of validation output.

#### Exception Summary (PHASE 5)

The `exception_summary` provides an aggregate view of system-level errors encountered during the validation session:

| Field | Description |
|-------|-------------|
| **total_exceptions** | Total number of exceptions encountered |
| **retried_count** | Number of validations that were retried |
| **recovered_count** | Number of validations that succeeded after retry |
| **permanent_failures** | Number of validations that failed permanently |
| **exceptions_by_type** | Distribution of exceptions by type (e.g., `TimeoutError`, `ConnectionError`) |
| **circuit_breaker_trips** | Number of times the circuit breaker was triggered |
| **skipped_by_dependency** | Number of validators skipped due to dependency failure |

### Issue Detail

Each detected issue is characterized by the following attributes. The enhanced issue model (PHASE 2 and PHASE 5) provides substantially richer diagnostic information.

| Attribute | Description | Phase |
|-----------|-------------|-------|
| **Column** | Name of the affected column (if applicable) | — |
| **Validator** | Name of the validator that detected the issue | — |
| **Severity** | critical, high, medium, or low | — |
| **Value** | The specific value or statistic that triggered the issue | — |
| **Description** | Human-readable explanation of the issue | — |
| **Row Count** | Number of rows affected (for row-level issues) | — |
| **validator_name** | Canonical name of the validator class that generated this issue | PHASE 2 |
| **success** | Boolean indicating whether this specific validation passed | PHASE 2 |
| **result** | Structured `ValidationDetail` object containing quantitative metrics | PHASE 2 |
| **exception_info** | Exception metadata for system-error issues (type, message, retry count, failure category) | PHASE 5 |

#### ValidationDetail Object (PHASE 2)

The `result` field on each issue contains a `ValidationDetail` object whose fields are progressively populated according to the selected `result_format` level:

| Field | Populated At | Description |
|-------|-------------|-------------|
| **element_count** | BOOLEAN_ONLY+ | Total number of rows evaluated |
| **missing_count** | BOOLEAN_ONLY+ | Number of null/missing values |
| **unexpected_count** | BOOLEAN_ONLY+ | Number of rows failing the validation predicate |
| **unexpected_percent** | BOOLEAN_ONLY+ | Failure rate relative to total row count |
| **unexpected_percent_nonmissing** | BOOLEAN_ONLY+ | Failure rate excluding null rows |
| **observed_value** | BASIC+ | The specific observed metric value |
| **partial_unexpected_list** | BASIC+ | Sample of failing values |
| **partial_unexpected_counts** | SUMMARY+ | Value-frequency pairs for failing values |
| **unexpected_rows** | COMPLETE | Full DataFrame of failing rows (serialized as dict list) |
| **debug_query** | COMPLETE | Reproducible query for failure row extraction |

### Severity Classification

Issues are classified into four severity levels, each corresponding to a distinct degree of data quality impact:

| Severity | Description | Visual |
|----------|-------------|--------|
| **Critical** | Data is fundamentally corrupt or unusable | Red |
| **High** | Significant quality issues that require attention | Orange |
| **Medium** | Moderate issues that may affect downstream processes | Yellow |
| **Low** | Minor issues or informational observations | Blue |

## Validation History and Longitudinal Analysis

The History page facilitates longitudinal analysis of validation results for a given data source.

### Temporal Controls

| Control | Options | Purpose |
|---------|---------|---------|
| **Period Selector** | Last 7, 30, or 90 days | Define the time window for analysis |
| **Granularity Selector** | Hourly, daily, or weekly | Control the aggregation granularity of trend charts |

### Summary Statistics

Four summary cards are presented, each displaying key metrics for the selected period:

| Metric | Description |
|--------|-------------|
| **Total Runs** | Number of validation executions in the period |
| **Success Rate** | Percentage of validations that passed |
| **Failure Rate** | Percentage of validations that failed |
| **Trend Direction** | Whether quality is improving (↑) or declining (↓) |

### Trend Visualization

The History page incorporates two chart types for the purposes of temporal analysis:

1. **Pass/Fail Rate Chart**: A line chart displaying the validation success and failure rates over time at the selected granularity
2. **Issue Frequency Chart**: A bar chart illustrating the frequency of different issue types, thereby enabling identification of recurring quality problems

### Recent Validations Table

A paginated table enumerates individual validation runs, with each entry comprising the following fields:

| Column | Description |
|--------|-------------|
| **Timestamp** | When the validation was executed |
| **Status** | Pass or fail |
| **Issue Count** | Number of issues detected |
| **Duration** | Execution time |
| **Validators** | Number of validators executed |

## Version Management and Snapshot Comparison

The Version History page enables the creation and comparative analysis of validation result snapshots.

### Version Creation

Validation results may be persisted as versioned snapshots for subsequent reference. This operation is initiated from the Validation Results page via the "Create Version" button. Each version captures the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Version Number** | Auto-incremented sequential identifier |
| **Timestamp** | Creation time of the snapshot |
| **Strategy** | Versioning strategy (incremental, semantic, timestamp, gitlike) |
| **Metadata** | Validation configuration and execution context |

### Versioning Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| **Incremental** | Simple sequential numbering | v1, v2, v3 |
| **Semantic** | Major.minor.patch version scheme | v1.0.0, v1.0.1, v1.1.0 |
| **Timestamp** | ISO 8601 timestamp-based identifiers | 2024-01-15T10:30:00 |
| **Git-like** | Short hash-based identifiers | a1b2c3d |

### Version Comparison

The comparison feature permits side-by-side analysis of two validation versions:

1. Two versions are selected from the timeline
2. The comparison view highlights differences in:
   - Overall pass/fail status
   - Issue counts by severity
   - Specific issues that appeared or disappeared
   - Changes in validation configuration

### Version Timeline

A visual timeline component renders all versions in chronological order, with version cards displaying:

- Version number and strategy badge
- Creation timestamp
- A concise summary of the validation state

## User-Defined Validation Rules

The Rules page exposes a YAML-based interface for the definition of user-specified validation rules.

### Rule Structure

Rules are expressed in YAML format and are organized into two sections:

```yaml
columns:
  email:
    - not_null
    - unique
    - pattern: "^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
  age:
    - not_null
    - min: 0
    - max: 150

table:
  - row_count_min: 100
  - no_duplicate_rows
```

### Rule Management

| Operation | Description |
|-----------|-------------|
| **Create Rule** | Define a new rule with name, description, and YAML definition |
| **Edit Rule** | Modify an existing rule's definition |
| **Delete Rule** | Remove a rule from the source |
| **Activate Rule** | Set a rule as the active validation rule for the source |

## Cross-Module Integration Points

### Schedule Integration

Validation configurations may be attached to [Schedules](../system/schedules.md) for automated periodic execution. The schedule persists the complete validator configuration, thereby ensuring consistent execution across successive runs.

### Notification Integration

Validation failures are capable of triggering [Notifications](../system/notifications.md) through configured channels. Notification rules support filtering by severity, source, and validator type.

### Alert Integration

Validation results are propagated into the [Unified Alert](../system/alerts.md) system, where they may be correlated with drift, anomaly, and model monitoring alerts.

## Recommended Operational Practices

| Practice | Recommendation |
|----------|----------------|
| **Start with Quick Check** | The Quick Check preset is recommended for initial quality assessment |
| **Customize Gradually** | Additional validators should be progressively enabled as the data is better understood |
| **Set Appropriate Severity** | Default severity levels should be overridden to reflect business criticality |
| **Version Important Results** | Version snapshots should be created before and after major data changes |
| **Monitor Trends** | The History page should be utilized to identify quality regression patterns |
| **Automate with Schedules** | Scheduled validations are recommended for production data sources |
| **Enable Parallel Execution** | Parallel mode should be employed for large datasets with many validators |

## API Reference

### Validation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/validate` | POST | Run validation on a data source |
| `/validations` | GET | List validation results |
| `/validations/{id}` | GET | Get validation result details |
| `/validations/{id}/issues` | GET | Get issues for a validation |

### History Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/history/sources/{id}` | GET | Get validation history for a source |
| `/history/sources/{id}/trends` | GET | Get trend data for a source |

### Version Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/versioning/sources/{id}` | GET | List versions for a source |
| `/versioning/sources/{id}` | POST | Create a new version snapshot |
| `/versioning/sources/{id}/compare` | GET | Compare two versions |
| `/versioning/{version_id}` | GET | Get version details |

### Rules Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/rules` | GET | List rules for a source |
| `/sources/{id}/rules` | POST | Create a new rule |
| `/rules/{id}` | PUT | Update a rule |
| `/rules/{id}` | DELETE | Delete a rule |
| `/rules/{id}/activate` | POST | Set as active rule |

## Truthound Core Engine Integration

The validation subsystem operates as a thin orchestration layer over the Truthound core engine (v1.3.0), which underwent a five-phase enhancement programme. The dashboard's backend adapter, converter, schemas, and frontend types were systematically extended in parallel to maintain full feature parity with each core engine phase. The following table summarises the integration scope:

| Dashboard Task | Core Phase | Integration Scope | Key Affected Files |
|----------------|------------|-------------------|--------------------|
| Task 1 | PHASE 1 — Result Format | Parameter propagation through all layers | `schemas/validation.py`, `truthound_adapter.py`, `services.py`, `validations.ts` |
| Task 2 | PHASE 2 — Structured Results | Schema extension for `ValidationDetail`, `ReportStatistics` | `converters/truthound.py`, `truthound_adapter.py`, `schemas/validation.py`, `validations.ts` |
| Task 3 | PHASE 3 — Metric Deduplication | No dashboard changes required (internal optimisation) | — |
| Task 4 | PHASE 4 — DAG Activation | Execution metadata (skipped validators, dependency graph) | `truthound_adapter.py`, `schemas/validation.py`, `validations.ts` |
| Task 5 | PHASE 5 — Exception Isolation | Exception transparency (capture, retry, circuit breaker) | `converters/truthound.py`, `truthound_adapter.py`, `schemas/validation.py`, `validations.ts`, `services.py` |

### Backward Compatibility

All integration changes adhere to a strict backward compatibility protocol:

- **Optional Fields**: Every field introduced through the enhancement phases is declared as `Optional` with a `None` default value, ensuring that pre-existing database records and API consumers remain functional.
- **Defensive Access**: The dashboard employs `getattr(issue, "field", default)` patterns to safely access fields that may be absent in older Truthound versions.
- **Pydantic Extra Ignore**: `model_config = ConfigDict(extra="ignore")` is applied to all schema classes, ensuring that unknown fields from future Truthound versions are silently discarded rather than raising validation errors.

### Data Flow Architecture

The validation data flow through the dashboard follows a six-stage pipeline:

```
Frontend (React/TypeScript)
  └─ ValidationRunOptions → POST /validations/sources/{id}/validate
        ↓
Backend (FastAPI)
  └─ api/validations.py → services.py → truthound_adapter.py
        ↓
  └─ truthound_adapter.check() → th.check(**kwargs)
        ↓
  └─ TruthoundResultConverter._convert_check_result() → CheckResult
        ↓
  └─ CheckResult.to_dict() → validation.result_json (SQLite JSON column)
        ↓
  └─ ValidationResponse.from_model() → JSON response → Frontend
```

The `TruthoundResultConverter` serves as the centralised translation boundary between the Truthound core engine's domain objects and the dashboard's Pydantic response models, ensuring that all five enhancement phases are uniformly represented in the API output.

## Glossary

| Term | Definition |
|------|------------|
| **Validation Run** | A single execution of one or more validators against a data source |
| **Issue** | A specific quality problem detected by a validator |
| **Severity** | Classification of an issue's impact (critical, high, medium, low) |
| **Version Snapshot** | A preserved copy of validation results for future reference |
| **Pushdown** | Optimization that executes validation logic directly on the database server |
| **Validator Config** | Per-validator parameter overrides applied during execution |
| **Result Format** | Progressive disclosure level controlling the granularity of validation output (PHASE 1) |
| **ValidationDetail** | Structured object containing quantitative validation metrics per issue (PHASE 2) |
| **ReportStatistics** | Aggregate statistical decomposition of a validation session (PHASE 2) |
| **DAG Execution** | Directed Acyclic Graph-based validator scheduling with dependency-driven conditional execution (PHASE 4) |
| **Exception Isolation** | Fault-tolerant execution mode that captures and classifies runtime errors without aborting the session (PHASE 5) |
| **Circuit Breaker** | Protective mechanism that suspends validator execution upon detecting repeated failures (PHASE 5) |
