# Getting Started

This guide describes the procedures for installing Truthound Dashboard and executing initial data validation operations.

## System Requirements

- Python 3.11 or higher
- pip (Python package manager)

## Installation

### Install from PyPI (Recommended)

```bash
pip install truthound-dashboard
```

This command automatically installs [truthound](https://github.com/seadonggyun4/truthound) as a transitive dependency.

### Install Development Version

```bash
git clone https://github.com/seadonggyun4/truthound-dashboard
cd truthound-dashboard
pip install -e ".[dev]"
```

## Quick Start

### 1. Launch the Dashboard

```bash
truthound serve
```

The browser opens automatically and the dashboard is accessible at `http://localhost:8765`.

### 2. Register a Data Source

1. Select **Data Sources** from the navigation menu
2. Click the **Add Source** button
3. Provide the required source information:
   - **Name**: A unique identifier for the data source (e.g., "Sales Data")
   - **Type**: Select the file or database type
   - **Config**: Enter type-specific connection parameters

**File Source Configuration Example:**
```json
{
  "path": "/path/to/your/data.csv"
}
```

**PostgreSQL Configuration Example:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "table": "sales"
}
```

### 3. Generate Schema Automatically

1. Navigate to the **Schema** tab for the registered source
2. Click the **Learn Schema** button
3. The system analyzes the data source and generates a schema definition

The generated schema includes:
- Column data types
- Nullable constraints
- Unique constraints
- Min/max value ranges for numeric columns
- Allowed values for low-cardinality columns

### 4. Execute Validation

1. Click the **Validate** button on the source detail page
2. Optionally expand **Advanced Options** to configure:
   - **Result Format**: Controls diagnostic detail level (`boolean_only`, `basic`, `summary`, `complete`)
   - **Include Unexpected Rows**: Attaches failure row data to results (for `summary` or higher)
   - **Catch Exceptions**: Enables fault-tolerant execution (errors are captured rather than aborting)
   - **Max Retries**: Number of automatic retry attempts for transient errors
3. Review the results upon completion

**Validation Result Fields:**
- **passed**: Boolean indicating overall pass/fail status
- **total_issues**: Aggregate count of detected issues
- **has_critical**: Presence of critical-severity issues
- **has_high**: Presence of high-severity issues
- **issues**: Detailed issue listing with per-column breakdown
- **statistics**: Aggregate validation statistics with multi-dimensional breakdowns (PHASE 2)
- **validator_execution_summary**: Validator execution states including skip reasons (PHASE 4)
- **exception_summary**: System error statistics with retry and recovery metrics (PHASE 5)

### 5. Configure Schedules (Optional)

To establish periodic validation execution:

1. Navigate to the **Schedules** menu
2. Click **Add Schedule**
3. Define the schedule using a cron expression

**Cron Expression Examples:**
- `0 9 * * *` — Daily at 09:00
- `0 */6 * * *` — Every 6 hours
- `0 0 * * 1` — Weekly on Monday at midnight

### 6. Configure Notifications (Optional)

To receive alerts upon validation failure:

1. Navigate to the **Notifications** menu
2. Click **Add Channel** to register a Slack, Email, or Webhook channel
3. Click **Add Rule** to configure notification trigger rules

## CLI Options

```bash
# Default execution (port 8765)
truthound serve

# Custom port
truthound serve --port 9000

# Allow external network access
truthound serve --host 0.0.0.0

# Suppress automatic browser invocation
truthound serve --no-browser

# Development mode (hot module replacement)
truthound serve --reload

# Specify data directory
truthound serve --data-dir /path/to/data
```

## Data Directory

Truthound Dashboard stores persistent data in `~/.truthound` by default:

```
~/.truthound/
├── dashboard.db    # SQLite database
├── logs/           # Log files
└── .key            # Encryption key (auto-generated)
```

## Next Steps

- [Features](./features.md) — Explore all capabilities
- [API Reference](./api.md) — Utilize the REST API
- [Configuration](./configuration.md) — Detailed configuration options

## Troubleshooting

### Port Already in Use

```bash
truthound serve --port 9000
```

### Database Reset

```bash
rm -rf ~/.truthound
truthound serve
```

### View Logs

```bash
cat ~/.truthound/logs/dashboard.log
```
