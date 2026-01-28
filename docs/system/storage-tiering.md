# Storage Tiering

The Storage Tiering module enables intelligent data lifecycle management by automatically moving data between storage tiers (Hot, Warm, Cold, Archive) based on configurable policies. This feature leverages the truthound library's storage tiering capabilities (truthound 1.2.10+) through a well-defined adapter pattern.

## Overview

Storage tiering optimizes storage costs and performance by placing data on appropriate storage tiers based on access patterns, age, or size. Data that is accessed frequently remains on fast, expensive storage (Hot tier), while older or less frequently accessed data migrates to cheaper, slower storage (Cold/Archive tiers).

## Architecture

The Storage Tiering system follows a layered architecture that promotes loose coupling and high extensibility:

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface Layer                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Tier Management │  │Policy Editor │  │ Migration Monitor │  │
│  └────────┬────────┘  └──────┬───────┘  └─────────┬─────────┘  │
└───────────┼──────────────────┼────────────────────┼─────────────┘
            │                  │                    │
┌───────────┼──────────────────┼────────────────────┼─────────────┐
│           ▼                  ▼                    ▼             │
│                       REST API Layer                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  /tiers  │  /policies  │  /execute  │  /status  │  /access │ │
│  └─────────────────────────────┬──────────────────────────────┘ │
└────────────────────────────────┼────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                                ▼                                 │
│                      Service Layer (TieringService)              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Policy Evaluation  │  Migration Orchestration  │  Access   │ │
│  │                     │                           │  Tracking │ │
│  └─────────────────────────────┬──────────────────────────────┘ │
└────────────────────────────────┼────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                                ▼                                 │
│                      Adapter Layer (TieringAdapter)              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Protocol-based Interface                       │ │
│  └──────────────────────┬─────────────────────────────────────┘ │
│                         │                                        │
│         ┌───────────────┴───────────────┐                       │
│         ▼                               ▼                        │
│  ┌──────────────────┐        ┌───────────────────┐              │
│  │ truthound.stores │        │ Fallback Impls    │              │
│  │    .tiering      │        │ (when unavailable)│              │
│  └──────────────────┘        └───────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Adapter Pattern** | TieringAdapter provides a stable interface regardless of truthound availability |
| **Graceful Degradation** | Fallback implementations ensure functionality when truthound is unavailable |
| **Protocol-based Interfaces** | Loose coupling through Python Protocol classes |
| **Separation of Concerns** | Clear boundaries between UI, API, Service, and Adapter layers |

## Key Concepts

### Storage Tiers

| Tier | Description | Use Case |
|------|-------------|----------|
| **Hot** | Fast, frequently accessed, expensive | Active production data |
| **Warm** | Moderate speed/cost | Recent historical data |
| **Cold** | Slow, rarely accessed, cheap | Compliance archives |
| **Archive** | Very slow, cheapest | Long-term retention |

### Migration Directions

| Direction | Description |
|-----------|-------------|
| **Demote** | Move to cheaper/slower tier (e.g., Hot → Cold) |
| **Promote** | Move to faster/more expensive tier (e.g., Cold → Hot) |

## Storage Tiering Interface

The Storage Tiering page is divided into four main sections accessible via tabs:

### 1. Storage Tiers Tab

Manage storage tier definitions and configurations.

| Field | Description |
|-------|-------------|
| **Name** | Human-readable tier name |
| **Tier Type** | hot, warm, cold, or archive |
| **Store Type** | Storage backend (file, s3, gcs, azure, etc.) |
| **Priority** | Tier priority for conflict resolution |
| **Cost per GB** | Optional cost tracking |
| **Retrieval Time (ms)** | Expected data access latency |
| **Active** | Enable/disable the tier |

### 2. Tier Policies Tab

Create and manage migration policies that define when and how data moves between tiers.

#### Policy Types

| Type | Description | Configuration |
|------|-------------|---------------|
| **Age-Based** | Migrate based on data age | `after_days`, `after_hours` |
| **Access-Based** | Migrate based on access patterns | `inactive_days`, `min_access_count`, `access_window_days` |
| **Size-Based** | Migrate based on data size | `min_size_bytes`, `tier_max_size_gb` |
| **Scheduled** | Migrate on specific days/times | `on_days`, `at_hour`, `min_age_days` |
| **Composite** | Combine multiple policies | `require_all` (AND/OR logic) |
| **Custom** | Custom predicate expression | `predicate_expression` |

#### Composite Policies (AND/OR Logic)

Composite policies enable complex migration rules by combining multiple child policies:

| Logic | Description |
|-------|-------------|
| **AND (require_all: true)** | All child policies must match for migration |
| **OR (require_all: false)** | Any child policy match triggers migration |

**Creating a Composite Policy:**

1. Select "Composite" as the policy type
2. Choose AND or OR logic mode
3. Add at least 2 child policies
4. Child policies can be any type except composite
5. The composite policy triggers based on the combined logic

**Example Use Cases:**

- **AND Logic**: Migrate only if data is >30 days old AND >1GB in size
- **OR Logic**: Migrate if data is >90 days old OR has <5 accesses in 30 days

### 3. Configurations Tab

Define global tiering settings that control how the tiering system operates.

| Setting | Description | Default |
|---------|-------------|---------|
| **Default Tier** | Initial tier for new data | Hot |
| **Enable Promotion** | Allow data to move to faster tiers | false |
| **Promotion Threshold** | Access count to trigger promotion | 10 |
| **Check Interval (hours)** | How often to evaluate policies | 24 |
| **Batch Size** | Items per migration batch | 100 |
| **Enable Parallel Migration** | Process multiple items concurrently | false |
| **Max Parallel Migrations** | Maximum concurrent migrations | 4 |

### 4. Migration History Tab

View historical migration operations with status tracking.

| Field | Description |
|-------|-------------|
| **Item ID** | Identifier of migrated item |
| **Policy** | Policy that triggered migration |
| **From → To Tier** | Source and destination tiers |
| **Size** | Data size transferred |
| **Status** | pending, in_progress, completed, failed |
| **Duration** | Time taken for migration |
| **Started At** | Timestamp of migration start |

## Policy Configuration Examples

### Age-Based Policy

```json
{
  "name": "Archive Old Data",
  "policy_type": "age_based",
  "from_tier_id": "hot-tier-id",
  "to_tier_id": "archive-tier-id",
  "direction": "demote",
  "config": {
    "after_days": 90
  }
}
```

### Access-Based Policy

```json
{
  "name": "Demote Inactive Data",
  "policy_type": "access_based",
  "from_tier_id": "hot-tier-id",
  "to_tier_id": "cold-tier-id",
  "direction": "demote",
  "config": {
    "inactive_days": 30,
    "min_access_count": 5,
    "access_window_days": 7
  }
}
```

### Size-Based Policy

```json
{
  "name": "Archive Large Files",
  "policy_type": "size_based",
  "from_tier_id": "warm-tier-id",
  "to_tier_id": "archive-tier-id",
  "direction": "demote",
  "config": {
    "min_size_gb": 10
  }
}
```

### Composite Policy (AND Logic)

```json
{
  "name": "Combined Criteria",
  "policy_type": "composite",
  "from_tier_id": "hot-tier-id",
  "to_tier_id": "cold-tier-id",
  "direction": "demote",
  "config": {
    "require_all": true
  }
}
```

Child policies are then linked via `parent_id` field.

### Scheduled Policy

```json
{
  "name": "Weekly Archive",
  "policy_type": "scheduled",
  "from_tier_id": "warm-tier-id",
  "to_tier_id": "archive-tier-id",
  "direction": "demote",
  "config": {
    "on_days": [0, 6],
    "at_hour": 3,
    "min_age_days": 30
  }
}
```

## Policy Execution

The Storage Tiering system supports both manual and automated policy execution, enabling operators to control when and how data migrations occur.

### Manual Execution

Operators can manually trigger policy execution through the dashboard or API. This is useful for:

- **On-demand migrations**: Moving data immediately without waiting for scheduled checks
- **Testing policies**: Verifying policy behavior before enabling automated execution
- **Emergency operations**: Quickly migrating data during incidents or capacity issues

#### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Execute** | Performs actual data migration | Production migrations |
| **Dry Run** | Simulates migration without moving data | Policy testing and impact analysis |

#### Dry Run (Simulation)

The dry run feature enables policy testing without affecting actual data. When executed in dry run mode:

1. The system evaluates all items against the policy criteria
2. Items that would be migrated are identified and counted
3. No actual data movement occurs
4. Results include item counts, estimated sizes, and migration paths

This capability is essential for:
- Validating policy configurations before production deployment
- Estimating migration impact on system resources
- Identifying unexpected items that match policy criteria

### Automated Execution

The background scheduler automatically evaluates and executes active policies based on configured intervals.

#### Scheduler Integration

| Setting | Description | Default |
|---------|-------------|---------|
| **Check Interval** | Frequency of policy evaluation | 1 hour |
| **Batch Processing** | Items processed per execution cycle | Configurable |
| **Error Handling** | Automatic retry with exponential backoff | Enabled |

The scheduler runs as part of the dashboard's background task system (APScheduler), ensuring consistent policy evaluation without manual intervention.

#### Execution Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Scheduler Trigger                          │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Load Active Policies                         │
│           (filter by is_active = true)                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              For Each Policy: Evaluate Items                  │
│   ┌────────────────────────────────────────────────────────┐ │
│   │  Age-Based → Check item age against threshold          │ │
│   │  Access-Based → Check access count and recency         │ │
│   │  Size-Based → Check item size against thresholds       │ │
│   │  Scheduled → Check if current time matches schedule    │ │
│   │  Composite → Evaluate child policies with AND/OR       │ │
│   │  Custom → Execute predicate expression                 │ │
│   └────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                Execute Migrations (Batched)                   │
│   - Transfer data from source to destination tier            │
│   - Update metadata store with new location                  │
│   - Record migration history                                 │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Return Execution Results                     │
│   - Items processed count                                    │
│   - Success/failure counts                                   │
│   - Total bytes migrated                                     │
└──────────────────────────────────────────────────────────────┘
```

## Intelligent Tiering with Access Tracking

The system supports intelligent tiering decisions based on actual data access patterns. This requires explicit access tracking, which can be enabled for applications that want promotion capabilities.

### Access Tracking

When data is accessed, applications can record the access event:

```
POST /tiering/items/{item_id}/access
```

This updates:
- **Last access timestamp**: When the item was last accessed
- **Access count**: Cumulative number of accesses
- **Access frequency**: Calculated metric for policy evaluation

### Promotion Criteria

Items can be promoted (moved to faster tiers) when:

| Criterion | Description |
|-----------|-------------|
| **Access Threshold** | Access count exceeds configured threshold |
| **Recency** | Recent access after period of inactivity |
| **Frequency** | High access frequency in observation window |

### Configuration

| Setting | Description |
|---------|-------------|
| `enable_promotion` | Allow data to move to faster tiers |
| `promotion_threshold` | Access count required for promotion |
| `access_window_days` | Time window for access frequency calculation |

## System Status and Health Monitoring

The system provides comprehensive status information for operational monitoring.

### Status Endpoint

```
GET /tiering/status
```

Returns:

| Field | Description |
|-------|-------------|
| `truthound_available` | Whether truthound tiering library is available |
| `tiering_enabled` | Whether tiering is actively processing |
| `scheduler_running` | Background scheduler status |
| `last_check_time` | Timestamp of last policy evaluation |
| `next_check_time` | Scheduled time for next evaluation |
| `active_migrations` | Currently running migration count |
| `migrations_24h` | Migration count in last 24 hours |

### Operational States

| State | Description | Indicator |
|-------|-------------|-----------|
| **Connected** | truthound library available, full functionality | Green |
| **Fallback** | Using fallback implementations | Yellow |
| **Disabled** | Tiering functionality disabled | Gray |
| **Error** | System error requiring attention | Red |

### Status Banner

The dashboard displays a status banner indicating the current operational state:

- **truthound Connected**: Full integration with truthound storage tiering
- **Using Fallback Mode**: Operating with built-in fallback implementations

## Statistics Dashboard

The Storage Tiering page displays real-time statistics:

| Metric | Description |
|--------|-------------|
| **Total Tiers** | Number of configured tiers |
| **Active Tiers** | Number of enabled tiers |
| **Total Policies** | Number of configured policies |
| **Composite Policies** | Number of composite policies |
| **Total Migrations** | Total migration count |
| **Successful Migrations** | Completed migrations |
| **Failed Migrations** | Failed migration count |
| **Total Bytes Migrated** | Data volume transferred |
| **Migrations (24h)** | Recent migration activity |

## Best Practices

### Tier Design

| Practice | Recommendation |
|----------|----------------|
| **Start Simple** | Begin with Hot and Archive tiers |
| **Add Gradients** | Introduce Warm/Cold as needs evolve |
| **Monitor Costs** | Track cost_per_gb for optimization |
| **Set Priorities** | Use priority for conflict resolution |

### Policy Design

| Practice | Recommendation |
|----------|----------------|
| **Test Policies** | Verify policies in non-production first |
| **Use Composite Wisely** | Avoid overly complex policy trees |
| **Monitor Migrations** | Watch for failed migrations |
| **Schedule Off-Peak** | Run migrations during low-activity periods |

### Performance Optimization

| Practice | Recommendation |
|----------|----------------|
| **Batch Appropriately** | Larger batches for bulk migrations |
| **Parallel Migration** | Enable for high-throughput systems |
| **Check Interval** | Balance frequency with system load |

## Troubleshooting

### Common Issues

| Issue | Resolution |
|-------|------------|
| **Migrations Not Running** | Verify policy is active and tiers exist |
| **High Failure Rate** | Check storage connectivity and permissions |
| **Slow Migrations** | Enable parallel migration, increase batch size |
| **Unexpected Demotions** | Review policy configurations and priorities |

### Migration Failures

When migrations fail:

1. Check the error message in Migration History
2. Verify source and destination tiers are accessible
3. Confirm sufficient storage capacity in destination tier
4. Check network connectivity for remote storage
5. Review application logs for detailed errors

## API Reference

### Storage Tiers

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/tiers` | GET | List all tiers |
| `/tiering/tiers` | POST | Create a tier |
| `/tiering/tiers/{id}` | GET | Get tier details |
| `/tiering/tiers/{id}` | PUT | Update tier |
| `/tiering/tiers/{id}` | DELETE | Delete tier |

### Tier Policies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/policies` | GET | List all policies |
| `/tiering/policies` | POST | Create a policy |
| `/tiering/policies/types` | GET | List policy types with schemas |
| `/tiering/policies/{id}` | GET | Get policy details |
| `/tiering/policies/{id}` | PUT | Update policy |
| `/tiering/policies/{id}` | DELETE | Delete policy |
| `/tiering/policies/{id}/tree` | GET | Get composite policy tree |

### Configurations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/configs` | GET | List all configurations |
| `/tiering/configs` | POST | Create a configuration |
| `/tiering/configs/{id}` | GET | Get configuration details |
| `/tiering/configs/{id}` | PUT | Update configuration |
| `/tiering/configs/{id}` | DELETE | Delete configuration |

### Migration History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/migrations` | GET | List migration history |
| `/tiering/migrations/{id}` | GET | Get migration details |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/stats` | GET | Get tiering statistics |

### Policy Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/policies/{id}/execute` | POST | Execute a specific policy |
| `/tiering/process` | POST | Process all active policies |
| `/tiering/status` | GET | Get system status |

**Execution Request Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `dry_run` | boolean | Simulate without actual migration |
| `batch_size` | integer | Items per batch (default: 100) |

**Execution Response:**

| Field | Description |
|-------|-------------|
| `policy_id` | Executed policy identifier |
| `items_evaluated` | Total items checked |
| `items_migrated` | Items successfully migrated |
| `items_failed` | Items that failed migration |
| `dry_run` | Whether this was a simulation |
| `errors` | List of error messages |

### Access Tracking

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/items/{id}/access` | POST | Record item access |
| `/tiering/items/{id}/migrate` | POST | Manually migrate item |

## truthound Integration

The Storage Tiering module integrates with truthound's storage tiering capabilities through the `TieringAdapter` class. This adapter provides:

### When truthound is Available

- **Full Feature Access**: All truthound tiering capabilities are utilized
- **Native Store Support**: S3, GCS, Azure Blob, file system stores
- **Advanced Policies**: Complex policy evaluation and composite logic
- **Optimized Migrations**: Efficient data transfer mechanisms

### When truthound is Unavailable

The system gracefully degrades to fallback implementations:

| Component | Fallback Behavior |
|-----------|-------------------|
| **Store** | In-memory data simulation |
| **StorageTier** | Basic tier metadata management |
| **Policy** | Simple policy evaluation |
| **MetadataStore** | Dictionary-based item tracking |
| **CompositePolicy** | AND/OR logic evaluation |

This ensures the dashboard remains functional for demonstration, testing, and development purposes even when truthound is not installed.

## Use Cases

### Cost Optimization

Automatically migrate aging data to cheaper storage tiers:

1. Configure Hot tier for active data (SSD, high IOPS)
2. Configure Cold tier for archives (Object storage, low cost)
3. Create age-based policy: migrate after 90 days
4. Enable automated execution

**Expected Outcome**: 40-60% reduction in storage costs for data older than 90 days.

### Compliance and Retention

Ensure data retention policies are enforced:

1. Configure Archive tier with write-once storage
2. Create scheduled policy: archive on first day of month
3. Set minimum age requirement: 1 year
4. Enable audit logging for compliance

**Expected Outcome**: Automated compliance with data retention regulations.

### Performance Optimization

Keep frequently accessed data on fast storage:

1. Enable access tracking in applications
2. Configure promotion threshold: 50 accesses
3. Enable `enable_promotion` in configuration
4. Create access-based demotion policy for inactive data

**Expected Outcome**: Hot tier contains only actively used data, improving overall system performance.

## Security Considerations

| Consideration | Recommendation |
|---------------|----------------|
| **Access Control** | Restrict policy execution to authorized operators |
| **Audit Logging** | Enable migration history for compliance |
| **Encryption** | Use encrypted storage backends for sensitive data |
| **Network Security** | Ensure secure connections to remote storage |

## Glossary

| Term | Definition |
|------|------------|
| **Tier** | A storage layer with specific performance and cost characteristics |
| **Policy** | A rule defining when and how data migrates between tiers |
| **Migration** | The process of moving data from one tier to another |
| **Demote** | Moving data to a cheaper/slower tier |
| **Promote** | Moving data to a faster/more expensive tier |
| **Dry Run** | Policy execution simulation without actual data movement |
| **Composite Policy** | A policy combining multiple child policies with AND/OR logic |
