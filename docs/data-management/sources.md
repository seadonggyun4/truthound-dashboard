# Data Sources

The Data Sources module provides comprehensive management capabilities for connecting to, configuring, and validating data sources within Truthound Dashboard.

## Overview

Data sources represent the fundamental entities upon which all validation, profiling, and quality monitoring operations are performed. The system supports a diverse range of data source types, including file-based sources (CSV, Parquet, JSON) and database connections (PostgreSQL, MySQL, Snowflake, BigQuery).

## Sources List Interface

### Source Listing

The main Sources page displays all registered data sources in a card-based layout. Each source card presents:

| Element | Description |
|---------|-------------|
| **Source Name** | User-defined identifier for the data source |
| **Type Badge** | Visual indicator of the connection type |
| **Description** | Optional descriptive text explaining the source's purpose |
| **Last Validation** | Timestamp of the most recent validation execution |
| **Status Indicator** | Color-coded badge reflecting validation status |

### Available Actions

From the source listing, users may perform the following operations:

- **Add Source**: Opens a dialog for registering a new data source
- **Validate**: Executes validation using default validator configuration
- **Delete**: Removes the source and all associated metadata (with confirmation)
- **View Details**: Navigates to the comprehensive Source Detail page

## Adding a Data Source

### Source Creation Dialog

The source creation workflow collects the following information:

1. **Source Name** (required): A unique identifier for the data source
2. **Source Type** (required): Selection from supported connection types
3. **Description** (optional): Explanatory text for documentation purposes
4. **Configuration** (required): Type-specific connection parameters

### Supported Source Types

| Type | Configuration Parameters |
|------|-------------------------|
| **CSV** | `path`: File system path to the CSV file |
| **Parquet** | `path`: File system path to the Parquet file |
| **JSON** | `path`: File system path to the JSON file |
| **PostgreSQL** | `host`, `port`, `database`, `username`, `password`, `table` |
| **MySQL** | `host`, `port`, `database`, `username`, `password`, `table` |
| **Snowflake** | `account`, `warehouse`, `database`, `schema`, `username`, `password`, `table` |
| **BigQuery** | `project`, `dataset`, `table`, `credentials_path` |

### Configuration Examples

**File Source (CSV)**:
```json
{
  "path": "/data/sales/transactions.csv"
}
```

**Database Source (PostgreSQL)**:
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "analytics",
  "username": "readonly_user",
  "password": "secure_password",
  "table": "customer_orders"
}
```

## Source Detail Interface

The Source Detail page provides comprehensive management and monitoring capabilities for individual data sources.

### Information Tabs

#### Connection Info Tab

Displays the source configuration with appropriate security measures:

- Sensitive fields (passwords, tokens, API keys) are masked by default
- Toggle visibility option for authorized review
- Connection type and configuration summary

#### Validation History Tab

Presents a chronological record of all validation executions:

| Column | Description |
|--------|-------------|
| **Timestamp** | Date and time of validation execution |
| **Status** | Pass/fail indicator |
| **Issues Count** | Total number of identified issues |
| **Duration** | Execution time in seconds |
| **Actions** | View detailed results |

#### Schema Tab

Displays the current schema definition for the source:

- Column names and data types
- Nullable constraints
- Unique constraints
- Value constraints (min/max, allowed values)

### Available Operations

#### Test Connection

Verifies connectivity to the data source without executing validation:

1. Click the **Test Connection** button
2. System attempts to establish connection using stored credentials
3. Success or failure notification is displayed
4. For failures, error details assist in troubleshooting

#### Learn Schema

Automatically generates a schema definition by analyzing the data source:

1. Click the **Learn Schema** button
2. System samples the data source to infer column types and constraints
3. Generated schema is displayed for review
4. Schema can be modified manually if required

#### Quick Validate

Executes validation using the default validator configuration:

1. Click the **Quick Validate** button
2. System runs all applicable validators
3. Results are displayed upon completion
4. Validation record is added to history

#### Configure & Run Validation

Provides granular control over validation execution:

1. Click the **Configure & Run** button
2. Select validators to execute from the validator registry (150+ available)
3. Configure validator-specific parameters (thresholds, columns, etc.)
4. Execute validation with custom configuration
5. Review results with detailed issue breakdown

### Preset Templates

The validator configuration dialog offers preset templates for common use cases:

| Template | Description |
|----------|-------------|
| **All Validators** | Executes all applicable validators |
| **Quick Check** | Essential validators for rapid assessment |
| **Schema Only** | Schema structure validation only |
| **Data Quality** | Comprehensive data quality validators |

### Edit Source

Modify source configuration:

1. Click the **Edit** button
2. Update source name, description, or configuration
3. Save changes
4. Re-test connection if configuration was modified

## Validation Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| **Success** | Green | Validation completed with no critical or high-severity issues |
| **Failed** | Red | Validation identified critical or high-severity issues |
| **Warning** | Yellow | Validation completed with medium or low-severity issues |
| **Pending** | Gray | No validation has been executed |

## Security Considerations

### Credential Storage

Connection credentials are encrypted using Fernet symmetric encryption before storage. The encryption key is automatically generated and stored with restricted file permissions in the Truthound data directory.

### Credential Display

Sensitive configuration fields are masked in the user interface by default. Users must explicitly toggle visibility to view credential values, providing protection against shoulder-surfing attacks.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources` | GET | List all data sources |
| `/sources` | POST | Create a new data source |
| `/sources/{id}` | GET | Retrieve source details |
| `/sources/{id}` | PUT | Update source configuration |
| `/sources/{id}` | DELETE | Delete a data source |
| `/sources/{id}/test` | POST | Test connection |
| `/validations/sources/{id}/validate` | POST | Execute validation |
| `/sources/{id}/learn` | POST | Generate schema automatically |
| `/sources/{id}/schema` | GET | Retrieve current schema |
| `/sources/{id}/profile` | POST | Generate basic data profile |
| `/sources/{id}/profile/advanced` | POST | Generate data profile with advanced configuration |
| `/scans/sources/{id}/scan` | POST | Scan for PII |
| `/masks/sources/{id}/mask` | POST | Mask sensitive data |
| `/drift/compare` | POST | Compare two sources for drift |

## Dashboard Extended API Parameters

The Dashboard extends the core Truthound library functions with additional parameters for enhanced flexibility. These extensions are available through the REST API.

### Schema Learning (`/sources/{id}/learn`)

Wraps `th.learn()` for automatic schema generation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `infer_constraints` | `bool` | `true` | Infer min/max and allowed values from data |
| `categorical_threshold` | `int` | `20` | Max unique values for categorical detection (1-1000) |

**Example Request:**
```json
{
  "infer_constraints": true,
  "categorical_threshold": 50
}
```

### Validation (`/validations/sources/{id}/validate`)

Wraps `th.check()` for data validation with configurable parameters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validators` | `list[str]` | `null` | Specific validators to run |
| `validator_config` | `dict` | `null` | Per-validator configuration (truthound 2.x format) |
| `min_severity` | `str` | `null` | Minimum severity to report (low/medium/high/critical) |
| `parallel` | `bool` | `false` | Enable parallel execution |
| `max_workers` | `int` | `null` | Max threads for parallel execution |
| `pushdown` | `bool` | `null` | Enable query pushdown for SQL sources |
| `schema` | `str` | `null` | Path to schema YAML file |
| `auto_schema` | `bool` | `false` | Auto-learn schema if not present |
| `custom_validators` | `list` | `null` | Custom validator configurations |

**Example Request:**
```json
{
  "validators": ["null", "duplicate", "range"],
  "validator_config": {
    "range": {"columns": {"age": {"min": 0, "max": 150}}}
  },
  "min_severity": "medium",
  "parallel": true,
  "max_workers": 4
}
```

### PII Scanning (`/scans/sources/{id}/scan`)

Wraps `th.scan()` for PII detection.

> **Note**: truthound's `th.scan()` does not support configuration parameters.
> The scan automatically runs on all columns with default settings, detecting all supported PII types.

**Example Request:**
```json
{}
```

### Data Masking (`/masks/sources/{id}/mask`)

Wraps `th.mask()` for data protection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | `list[str]` | `null` | Columns to mask (auto-detect if null) |
| `strategy` | `str` | `"redact"` | Masking strategy (redact/hash/fake) |

> **Note**: truthound's `th.mask()` does not support output format selection.
> The output is always generated in CSV format.

**Example Request:**
```json
{
  "columns": ["ssn", "credit_card", "email"],
  "strategy": "hash"
}
```

### Data Profiling (`/sources/{id}/profile`)

Wraps `th.profile()` for basic data profiling with default settings.

**Example Request:**
```json
{}
```

### Advanced Data Profiling (`/sources/{id}/profile/advanced`)

Uses truthound's `ProfilerConfig` for fine-grained control over profiling behavior.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sample_size` | `int` | `null` | Maximum rows to sample (null for all rows) |
| `random_seed` | `int` | `42` | Random seed for reproducible sampling |
| `include_patterns` | `bool` | `true` | Enable pattern detection (email, phone, uuid, etc.) |
| `include_correlations` | `bool` | `false` | Calculate column correlations |
| `include_distributions` | `bool` | `true` | Include value distribution histograms |
| `top_n_values` | `int` | `10` | Number of top values to return per column |
| `pattern_sample_size` | `int` | `1000` | Sample size for pattern detection |
| `correlation_threshold` | `float` | `0.7` | Minimum correlation to report |
| `min_pattern_match_ratio` | `float` | `0.8` | Minimum match ratio for pattern detection |
| `n_jobs` | `int` | `1` | Number of parallel jobs for profiling |

**Example Request:**
```json
{
  "sample_size": 50000,
  "include_patterns": true,
  "include_correlations": true,
  "include_distributions": true,
  "top_n_values": 20,
  "n_jobs": 4
}
```

> **Note**: Advanced profiling requires truthound with ProfilerConfig support. If not available, the API returns a 501 error.

The profile response includes:
- Column types and inferred semantic types
- Null and unique value percentages
- Statistical measures (min, max, mean, std, median, quartiles)
- String length statistics
- Detected patterns (email, phone, UUID, etc.)
- Value distribution histograms
- Column correlations (when `include_correlations` is true)

### Drift Detection (`/drift/compare`)

Wraps `th.compare()` for distribution comparison between datasets.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `baseline_source_id` | `str` | Required | Baseline source ID |
| `current_source_id` | `str` | Required | Current source ID |
| `columns` | `list[str]` | `null` | Columns to compare |
| `method` | `str` | `"auto"` | Detection method (auto/ks/psi/chi2/js/kl/wasserstein/cvm/anderson/hellinger/bhattacharyya/tv/energy/mmd) |
| `threshold` | `float` | `null` | Custom drift threshold |
| `sample_size` | `int` | `null` | Sample size for large datasets |

**Detection Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| `auto` | Automatic selection based on dtype | General use |
| `ks` | Kolmogorov-Smirnov test | Continuous numeric |
| `psi` | Population Stability Index | ML monitoring |
| `chi2` | Chi-squared test | Categorical |
| `js` | Jensen-Shannon divergence | Any distribution |
| `kl` | Kullback-Leibler divergence | Information-theoretic |
| `wasserstein` | Wasserstein distance | Distribution shape |
| `cvm` | Cramér-von Mises test | Continuous distributions |
| `anderson` | Anderson-Darling test | Tail-sensitive detection |
| `hellinger` | Hellinger distance | Bounded metric |
| `bhattacharyya` | Bhattacharyya distance | Classification bounds |
| `tv` | Total Variation distance | Maximum difference |
| `energy` | Energy distance | Location/scale |
| `mmd` | Maximum Mean Discrepancy | High-dimensional |

**Example Request:**
```json
{
  "baseline_source_id": "abc-123",
  "current_source_id": "def-456",
  "columns": ["age", "income", "score"],
  "method": "psi",
  "sample_size": 10000
}
