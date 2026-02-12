# Storage Tiering

The Storage Tiering module facilitates intelligent data lifecycle management through the automated migration of data across hierarchically organized storage tiers (Hot, Warm, Cold, Archive) in accordance with configurable policy specifications. This capability is realized through integration with the truthound library's storage tiering subsystem (truthound 1.2.10+) via a well-defined adapter pattern.

## Introduction and Scope

Storage tiering is employed to optimize the balance between storage expenditure and access performance by placing data on storage tiers commensurate with observed access patterns, temporal age, or volumetric characteristics. Data that is accessed with high frequency is retained on performant, higher-cost storage media (Hot tier), whereas data exhibiting lower access frequency or greater temporal age is progressively migrated to more economical, higher-latency storage media (Cold/Archive tiers).

## Architectural Overview

The Storage Tiering system is organized according to a layered architecture that promotes loose coupling and high extensibility:

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

### Governing Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Adapter Pattern** | TieringAdapter provides a stable interface regardless of truthound availability |
| **Graceful Degradation** | Fallback implementations ensure functionality when truthound is unavailable |
| **Protocol-based Interfaces** | Loose coupling through Python Protocol classes |
| **Separation of Concerns** | Clear boundaries between UI, API, Service, and Adapter layers |

## Fundamental Concepts

### Storage Tier Architecture

| Tier | Description | Use Case |
|------|-------------|----------|
| **Hot** | Fast, frequently accessed, expensive | Active production data |
| **Warm** | Moderate speed/cost | Recent historical data |
| **Cold** | Slow, rarely accessed, cheap | Compliance archives |
| **Archive** | Very slow, cheapest | Long-term retention |

### Migration Directionality

| Direction | Description |
|-----------|-------------|
| **Demote** | Move to cheaper/slower tier (e.g., Hot → Cold) |
| **Promote** | Move to faster/more expensive tier (e.g., Cold → Hot) |

## Storage Tiering User Interface

The Storage Tiering page is organized into four principal sections, each accessible through a dedicated tab interface:

### 1. Storage Tiers Management Tab

This tab is provided for the administration of storage tier definitions and their associated configurations.

| Field | Description |
|-------|-------------|
| **Name** | Human-readable tier name |
| **Tier Type** | hot, warm, cold, or archive |
| **Store Type** | Storage backend (file, s3, gcs, azure, etc.) |
| **Priority** | Tier priority for conflict resolution |
| **Cost per GB** | Optional cost tracking |
| **Retrieval Time (ms)** | Expected data access latency |
| **Active** | Enable/disable the tier |

### 2. Tier Policies Management Tab

This tab facilitates the creation and management of migration policies that govern the conditions under which data is transferred between tiers.

#### Policy Type Taxonomy

| Type | Description | Configuration |
|------|-------------|---------------|
| **Age-Based** | Migrate based on data age | `after_days`, `after_hours` |
| **Access-Based** | Migrate based on access patterns | `inactive_days`, `min_access_count`, `access_window_days` |
| **Size-Based** | Migrate based on data size | `min_size_bytes`, `tier_max_size_gb` |
| **Scheduled** | Migrate on specific days/times | `on_days`, `at_hour`, `min_age_days` |
| **Composite** | Combine multiple policies | `require_all` (AND/OR logic) |
| **Custom** | Custom predicate expression | `predicate_expression` |

#### Composite Policy Specification (Conjunctive and Disjunctive Logic)

Composite policies enable the construction of complex migration rules through the combination of multiple subordinate (child) policies:

| Logic | Description |
|-------|-------------|
| **AND (require_all: true)** | All child policies must match for migration |
| **OR (require_all: false)** | Any child policy match triggers migration |

**Procedure for Composite Policy Construction:**

1. Select "Composite" as the policy type
2. Choose AND or OR logic mode
3. Add at least 2 child policies
4. Child policies can be any type except composite
5. The composite policy triggers based on the combined logic

**Illustrative Use Cases:**

- **AND Logic**: Migrate only if data is >30 days old AND >1GB in size
- **OR Logic**: Migrate if data is >90 days old OR has <5 accesses in 30 days

### 3. Global Configuration Tab

This tab is designated for the definition of global tiering parameters that govern the operational behavior of the tiering subsystem.

| Setting | Description | Default |
|---------|-------------|---------|
| **Default Tier** | Initial tier for new data | Hot |
| **Enable Promotion** | Allow data to move to faster tiers | false |
| **Promotion Threshold** | Access count to trigger promotion | 10 |
| **Check Interval (hours)** | How often to evaluate policies | 24 |
| **Batch Size** | Items per migration batch | 100 |
| **Enable Parallel Migration** | Process multiple items concurrently | false |
| **Max Parallel Migrations** | Maximum concurrent migrations | 4 |

### 4. Migration History and Audit Tab

This tab provides a chronological record of historical migration operations along with their associated status indicators.

| Field | Description |
|-------|-------------|
| **Item ID** | Identifier of migrated item |
| **Policy** | Policy that triggered migration |
| **From → To Tier** | Source and destination tiers |
| **Size** | Data size transferred |
| **Status** | pending, in_progress, completed, failed |
| **Duration** | Time taken for migration |
| **Started At** | Timestamp of migration start |

## Policy Configuration Specifications

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

### Composite Policy (Conjunctive Logic)

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

Child policies are subsequently associated via the `parent_id` field.

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

## Policy Execution Framework

The Storage Tiering system accommodates both manual and automated policy execution paradigms, thereby affording operators comprehensive control over the timing and methodology of data migrations.

### Manual Execution

Operators may manually initiate policy execution through the dashboard interface or the REST API. This operational mode is particularly suited to the following scenarios:

- **On-demand migrations**: Effecting immediate data movement without awaiting scheduled evaluation cycles
- **Policy verification**: Validating policy behavior prior to the enablement of automated execution
- **Emergency operations**: Expeditiously migrating data during incidents or capacity constraint events

#### Execution Modalities

| Mode | Description | Use Case |
|------|-------------|----------|
| **Execute** | Performs actual data migration | Production migrations |
| **Dry Run** | Simulates migration without moving data | Policy testing and impact analysis |

#### Dry Run Simulation

The dry run capability enables policy validation without affecting the state of actual data. When a policy is executed in dry run mode, the following sequence is observed:

1. The system evaluates all items against the policy criteria
2. Items that would be migrated are identified and counted
3. No actual data movement occurs
4. Results include item counts, estimated sizes, and migration paths

This capability is considered essential for the following purposes:
- Validating policy configurations prior to production deployment
- Estimating the resource impact of proposed migrations
- Identifying items that unexpectedly satisfy policy criteria

### Automated Execution

The background scheduler is responsible for the automatic evaluation and execution of active policies at configured intervals.

#### Scheduler Integration

| Setting | Description | Default |
|---------|-------------|---------|
| **Check Interval** | Frequency of policy evaluation | 1 hour |
| **Batch Processing** | Items processed per execution cycle | Configurable |
| **Error Handling** | Automatic retry with exponential backoff | Enabled |

The scheduler operates as a constituent component of the dashboard's background task infrastructure (APScheduler), thereby ensuring consistent policy evaluation without necessitating manual intervention.

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

## Intelligent Tiering via Access Pattern Analysis

The system supports intelligent tiering decisions informed by observed data access patterns. This functionality requires the explicit enablement of access tracking, which may be configured for applications that necessitate promotion capabilities.

### Access Event Recording

When data is accessed, applications may record the access event through the designated endpoint:

```
POST /tiering/items/{item_id}/access
```

This operation updates the following metrics:
- **Last access timestamp**: The temporal coordinate of the most recent access event
- **Access count**: The cumulative total of access events recorded
- **Access frequency**: A derived metric employed in policy evaluation

### Promotion Criteria

Items may be promoted (i.e., migrated to a higher-performance tier) when the following criteria are satisfied:

| Criterion | Description |
|-----------|-------------|
| **Access Threshold** | Access count exceeds configured threshold |
| **Recency** | Recent access after period of inactivity |
| **Frequency** | High access frequency in observation window |

### Promotion Configuration Parameters

| Setting | Description |
|---------|-------------|
| `enable_promotion` | Allow data to move to faster tiers |
| `promotion_threshold` | Access count required for promotion |
| `access_window_days` | Time window for access frequency calculation |

## System Status and Health Monitoring

The system provides comprehensive status telemetry for the purposes of operational monitoring and diagnostics.

### Status Endpoint

```
GET /tiering/status
```

The following fields are returned:

| Field | Description |
|-------|-------------|
| `truthound_available` | Whether truthound tiering library is available |
| `tiering_enabled` | Whether tiering is actively processing |
| `scheduler_running` | Background scheduler status |
| `last_check_time` | Timestamp of last policy evaluation |
| `next_check_time` | Scheduled time for next evaluation |
| `active_migrations` | Currently running migration count |
| `migrations_24h` | Migration count in last 24 hours |

### Operational State Classification

| State | Description | Indicator |
|-------|-------------|-----------|
| **Connected** | truthound library available, full functionality | Green |
| **Fallback** | Using fallback implementations | Yellow |
| **Disabled** | Tiering functionality disabled | Gray |
| **Error** | System error requiring attention | Red |

### Status Banner

The dashboard renders a status banner that communicates the current operational state of the tiering subsystem:

- **truthound Connected**: Full integration with truthound storage tiering is established
- **Using Fallback Mode**: The system is operating with built-in fallback implementations

## Statistical Monitoring Dashboard

The Storage Tiering page presents the following real-time statistical indicators:

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

## Recommended Operational Practices

### Tier Design Considerations

| Practice | Recommendation |
|----------|----------------|
| **Start Simple** | Begin with Hot and Archive tiers |
| **Add Gradients** | Introduce Warm/Cold as needs evolve |
| **Monitor Costs** | Track cost_per_gb for optimization |
| **Set Priorities** | Use priority for conflict resolution |

### Policy Design Considerations

| Practice | Recommendation |
|----------|----------------|
| **Test Policies** | Verify policies in non-production first |
| **Use Composite Wisely** | Avoid overly complex policy trees |
| **Monitor Migrations** | Watch for failed migrations |
| **Schedule Off-Peak** | Run migrations during low-activity periods |

### Performance Optimization Considerations

| Practice | Recommendation |
|----------|----------------|
| **Batch Appropriately** | Larger batches for bulk migrations |
| **Parallel Migration** | Enable for high-throughput systems |
| **Check Interval** | Balance frequency with system load |

## Troubleshooting and Diagnostics

### Commonly Encountered Issues

| Issue | Resolution |
|-------|------------|
| **Migrations Not Running** | Verify policy is active and tiers exist |
| **High Failure Rate** | Check storage connectivity and permissions |
| **Slow Migrations** | Enable parallel migration, increase batch size |
| **Unexpected Demotions** | Review policy configurations and priorities |

### Migration Failure Resolution Procedure

When migration failures are encountered, the following diagnostic procedure is recommended:

1. Examine the error message recorded in the Migration History
2. Verify that both source and destination tiers are accessible
3. Confirm that sufficient storage capacity exists in the destination tier
4. Validate network connectivity for remote storage backends
5. Consult application logs for detailed error diagnostics

## API Reference

### Storage Tier Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/tiers` | GET | List all tiers |
| `/tiering/tiers` | POST | Create a tier |
| `/tiering/tiers/{id}` | GET | Get tier details |
| `/tiering/tiers/{id}` | PUT | Update tier |
| `/tiering/tiers/{id}` | DELETE | Delete tier |

### Tier Policy Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/policies` | GET | List all policies |
| `/tiering/policies` | POST | Create a policy |
| `/tiering/policies/types` | GET | List policy types with schemas |
| `/tiering/policies/{id}` | GET | Get policy details |
| `/tiering/policies/{id}` | PUT | Update policy |
| `/tiering/policies/{id}` | DELETE | Delete policy |
| `/tiering/policies/{id}/tree` | GET | Get composite policy tree |

### Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/configs` | GET | List all configurations |
| `/tiering/configs` | POST | Create a configuration |
| `/tiering/configs/{id}` | GET | Get configuration details |
| `/tiering/configs/{id}` | PUT | Update configuration |
| `/tiering/configs/{id}` | DELETE | Delete configuration |

### Migration History Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/migrations` | GET | List migration history |
| `/tiering/migrations/{id}` | GET | Get migration details |

### Statistical Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/stats` | GET | Get tiering statistics |

### Policy Execution Endpoints

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

**Execution Response Schema:**

| Field | Description |
|-------|-------------|
| `policy_id` | Executed policy identifier |
| `items_evaluated` | Total items checked |
| `items_migrated` | Items successfully migrated |
| `items_failed` | Items that failed migration |
| `dry_run` | Whether this was a simulation |
| `errors` | List of error messages |

### Access Tracking Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tiering/items/{id}/access` | POST | Record item access |
| `/tiering/items/{id}/migrate` | POST | Manually migrate item |

## truthound Library Integration

The Storage Tiering module is integrated with the truthound library's storage tiering capabilities through the `TieringAdapter` class. The adapter provides the following functionality:

### Behavior When truthound Is Available

- **Full Feature Access**: All truthound tiering capabilities are utilized
- **Native Store Support**: S3, GCS, Azure Blob, file system stores
- **Advanced Policies**: Complex policy evaluation and composite logic
- **Optimized Migrations**: Efficient data transfer mechanisms

### Graceful Degradation When truthound Is Unavailable

The system degrades gracefully to fallback implementations in the absence of the truthound library:

| Component | Fallback Behavior |
|-----------|-------------------|
| **Store** | In-memory data simulation |
| **StorageTier** | Basic tier metadata management |
| **Policy** | Simple policy evaluation |
| **MetadataStore** | Dictionary-based item tracking |
| **CompositePolicy** | AND/OR logic evaluation |

This design ensures that the dashboard remains fully functional for demonstration, testing, and development purposes even in environments where the truthound library has not been installed.

## Representative Use Cases

### Cost Optimization

The following procedure illustrates the automated migration of aging data to lower-cost storage tiers:

1. Configure Hot tier for active data (SSD, high IOPS)
2. Configure Cold tier for archives (Object storage, low cost)
3. Create age-based policy: migrate after 90 days
4. Enable automated execution

**Expected Outcome**: 40-60% reduction in storage costs for data older than 90 days.

### Regulatory Compliance and Data Retention

The following procedure ensures the enforcement of data retention policies:

1. Configure Archive tier with write-once storage
2. Create scheduled policy: archive on first day of month
3. Set minimum age requirement: 1 year
4. Enable audit logging for compliance

**Expected Outcome**: Automated compliance with data retention regulations.

### Performance Optimization

The following procedure ensures that frequently accessed data is maintained on high-performance storage:

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

## Glossary of Terms

| Term | Definition |
|------|------------|
| **Tier** | A storage layer with specific performance and cost characteristics |
| **Policy** | A rule defining when and how data migrates between tiers |
| **Migration** | The process of moving data from one tier to another |
| **Demote** | Moving data to a cheaper/slower tier |
| **Promote** | Moving data to a faster/more expensive tier |
| **Dry Run** | Policy execution simulation without actual data movement |
| **Composite Policy** | A policy combining multiple child policies with AND/OR logic |
