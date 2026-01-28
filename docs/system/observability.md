# Observability

The Observability module provides comprehensive system monitoring capabilities through three interconnected pillars: Audit Logging, Metrics Collection, and Distributed Tracing. This feature leverages truthound's store observability infrastructure to deliver enterprise-grade visibility into system operations.

## Overview

Observability in modern data quality systems extends beyond traditional monitoring by providing deep insights into system behavior, performance characteristics, and operational patterns. The Truthound Dashboard implements the three pillars of observability to enable administrators to understand not just *what* happened, but *why* it happened.

### The Three Pillars of Observability

| Pillar | Purpose | Key Questions Answered |
|--------|---------|------------------------|
| **Audit Logging** | Immutable record of all operations | Who did what, when, and what was the outcome? |
| **Metrics** | Quantitative measurements over time | How is the system performing? What are the trends? |
| **Tracing** | Request flow across components | Where are bottlenecks? How do operations flow? |

## Theoretical Foundation

### Audit Logging

Audit logging provides a chronological, immutable record of all significant operations within the system. Unlike application logs designed for debugging, audit logs serve compliance, security, and operational analysis purposes.

#### Audit Event Model

Each audit event captures contextual information following the W5 principle:

| Dimension | Field | Description |
|-----------|-------|-------------|
| **Who** | `user_id`, `session_id` | Identity of the actor |
| **What** | `event_type`, `store_type` | Operation performed |
| **When** | `timestamp` | Precise occurrence time |
| **Where** | `store_id`, `item_id` | Target of the operation |
| **Why/Result** | `status`, `error_message` | Outcome and context |

#### Event Types

| Category | Event Types | Description |
|----------|-------------|-------------|
| **CRUD Operations** | create, read, update, delete | Standard data operations |
| **Batch Operations** | batch_create, batch_delete | Bulk data modifications |
| **Query Operations** | query, list, count | Data retrieval operations |
| **Lifecycle Events** | initialize, close, flush | Store lifecycle management |
| **Sync Operations** | replicate, sync, migrate, rollback | Data synchronization |
| **Access Control** | access_denied, access_granted | Security-related events |
| **Errors** | error, validation_error | Failure conditions |

#### Audit Status Classification

| Status | Description | Use Case |
|--------|-------------|----------|
| **Success** | Operation completed normally | Standard operations |
| **Failure** | Operation failed with error | Error analysis |
| **Partial** | Batch operation partially succeeded | Batch processing |
| **Denied** | Operation rejected by access control | Security monitoring |

### Metrics Collection

Metrics provide quantitative measurements that enable trend analysis, capacity planning, and performance optimization. The system collects four metric types following the RED and USE methodologies.

#### Metric Types

| Type | Description | Example |
|------|-------------|---------|
| **Counter** | Monotonically increasing value | Total operations, errors |
| **Gauge** | Point-in-time measurement | Active connections, cache size |
| **Histogram** | Distribution of values | Request latency distribution |
| **Summary** | Statistical summary with quantiles | Response time percentiles |

#### Store Metrics

| Metric Category | Metrics | Purpose |
|-----------------|---------|---------|
| **Operations** | operations_total, operations_by_type | Throughput analysis |
| **I/O** | bytes_read_total, bytes_written_total | Data transfer volume |
| **Connections** | active_connections | Resource utilization |
| **Cache** | cache_hits, cache_misses, cache_hit_rate | Cache effectiveness |
| **Errors** | errors_total, errors_by_type | Reliability analysis |
| **Latency** | avg_operation_duration_ms | Performance tracking |

#### Cache Hit Rate Analysis

The cache hit rate is a critical metric for understanding system efficiency:

| Hit Rate | Interpretation | Recommended Action |
|----------|----------------|-------------------|
| **> 90%** | Excellent | Maintain current configuration |
| **70-90%** | Good | Monitor for degradation |
| **50-70%** | Acceptable | Consider cache size increase |
| **< 50%** | Poor | Review access patterns, increase cache |

### Distributed Tracing

Distributed tracing provides visibility into request flows across system components, enabling identification of latency bottlenecks and failure points.

#### Tracing Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | End-to-end journey of a request |
| **Span** | Single unit of work within a trace |
| **Context** | Propagated metadata (trace_id, span_id) |
| **Parent Span** | The span that initiated the current span |

#### Span Types (SpanKind)

| Kind | Description | Use Case |
|------|-------------|----------|
| **Internal** | Internal operation | Business logic processing |
| **Server** | Server-side handler | API endpoint processing |
| **Client** | Client-side request | External service calls |
| **Producer** | Message producer | Async message sending |
| **Consumer** | Message consumer | Async message processing |

## Observability Interface

The Observability page provides a unified view organized into five tabs.

### 1. Overview Tab

Displays key statistics from all three observability pillars:

| Card | Metrics | Purpose |
|------|---------|---------|
| **Total Events** | Audit event count | Volume indicator |
| **Events Today** | Today's event count | Current activity |
| **Error Rate** | Failure percentage | System health |
| **Cache Hit Rate** | Cache effectiveness | Performance indicator |

### 2. Audit Tab

Provides audit event exploration with filtering capabilities.

#### Filter Options

| Filter | Description |
|--------|-------------|
| **Event Type** | Filter by specific operation type |
| **Status** | Filter by outcome (success, failure, partial, denied) |
| **Time Range** | Filter by start and end time |
| **Item ID** | Filter by specific data item |

#### Audit Table Columns

| Column | Description |
|--------|-------------|
| **Event ID** | Unique identifier |
| **Type** | Operation type |
| **Timestamp** | When the event occurred |
| **Status** | Operation outcome |
| **Store** | Target store type |
| **Duration** | Operation duration in milliseconds |

### 3. Metrics Tab

Displays store-level metrics organized by category.

#### Operations Metrics

| Metric | Description |
|--------|-------------|
| **Operations Total** | Cumulative operation count |
| **Operations by Type** | Breakdown by operation type |

#### I/O Metrics

| Metric | Description |
|--------|-------------|
| **Bytes Read** | Total data read volume |
| **Bytes Written** | Total data written volume |

#### Cache Metrics

| Metric | Description |
|--------|-------------|
| **Cache Hits** | Successful cache retrievals |
| **Cache Misses** | Cache misses requiring data fetch |
| **Hit Rate** | Percentage of successful cache hits |

#### Error Metrics

| Metric | Description |
|--------|-------------|
| **Errors Total** | Cumulative error count |
| **Errors by Type** | Breakdown by error category |

### 4. Tracing Tab

Displays distributed tracing statistics when tracing is enabled.

| Metric | Description |
|--------|-------------|
| **Total Traces** | Number of complete traces |
| **Total Spans** | Number of individual spans |
| **Avg Trace Duration** | Average end-to-end latency |
| **Traces Today** | Today's trace count |
| **Error Rate** | Percentage of failed spans |
| **By Service** | Breakdown by service name |

### 5. Config Tab

Enables configuration of observability features.

#### Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| **Enable Audit** | Boolean | true | Toggle audit logging |
| **Enable Metrics** | Boolean | true | Toggle metrics collection |
| **Enable Tracing** | Boolean | false | Toggle distributed tracing |
| **Audit Log Path** | String | null | File path for audit log persistence |
| **Audit Rotate Daily** | Boolean | false | Enable daily log rotation |
| **Audit Max Events** | Integer | 10000 | Maximum events in memory |
| **Redact Fields** | Array | [] | Fields to redact from audit logs |
| **Metrics Prefix** | String | "truthound" | Prefix for metric names |
| **Tracing Service Name** | String | "dashboard" | Service identifier in traces |
| **Tracing Endpoint** | String | null | OpenTelemetry collector endpoint |

## Data Privacy and Redaction

The observability system supports field-level redaction to protect sensitive data in audit logs.

### Redaction Configuration

Configure fields to be automatically redacted:

| Field Type | Example Fields | Redaction Behavior |
|------------|----------------|-------------------|
| **Authentication** | password, token, api_key | Replace with `[REDACTED]` |
| **PII** | ssn, email, phone | Replace with `[REDACTED]` |
| **Financial** | credit_card, account_number | Replace with `[REDACTED]` |

### Redaction Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Default Redaction** | Configure common sensitive fields globally |
| **Audit Review** | Periodically review logs for data leakage |
| **Compliance Alignment** | Match redaction to regulatory requirements |

## Operational Best Practices

### Audit Log Management

| Practice | Recommendation |
|----------|----------------|
| **Retention** | Define retention aligned with compliance |
| **Rotation** | Enable daily rotation for large deployments |
| **Analysis** | Regular review of error and denial patterns |
| **Archival** | Archive old logs to cold storage |

### Metrics Utilization

| Practice | Recommendation |
|----------|----------------|
| **Baseline** | Establish normal operating baselines |
| **Alerting** | Configure alerts for metric anomalies |
| **Trending** | Track metrics over time for capacity planning |
| **Dashboard** | Create role-specific metric dashboards |

### Tracing Implementation

| Practice | Recommendation |
|----------|----------------|
| **Sampling** | Use sampling for high-volume systems |
| **Context Propagation** | Ensure trace context flows across boundaries |
| **Span Naming** | Use consistent, descriptive span names |
| **Error Tagging** | Tag spans with error information |

## Integration with truthound

The Observability module integrates with truthound's store observability infrastructure:

### Store Manager Integration

The dashboard's `StoreManager` provides layered observability:

| Layer | Component | Function |
|-------|-----------|----------|
| **Base** | Store | Core data operations |
| **Versioning** | VersionedStore | Change tracking |
| **Caching** | CachedStore | Performance optimization |
| **Tiering** | TieredStore | Data lifecycle management |
| **Observability** | AuditLogger, Metrics | Monitoring |

### Audit Logger

The truthound `AuditLogger` automatically captures:

- All store CRUD operations
- Operation timing and duration
- Success and failure outcomes
- User and session context

### Metrics Collector

The truthound metrics system provides:

- Automatic metric instrumentation
- Prometheus-compatible metric format
- Histogram buckets for latency distribution
- Label-based metric dimensions

## Troubleshooting

### Common Issues

| Issue | Resolution |
|-------|------------|
| **Missing Audit Events** | Verify audit logging is enabled |
| **High Error Rate** | Review error_message in audit events |
| **Low Cache Hit Rate** | Increase cache size or TTL |
| **Tracing Not Working** | Verify tracing endpoint configuration |

### Performance Considerations

| Concern | Mitigation |
|---------|------------|
| **Audit Log Growth** | Enable rotation, configure max_events |
| **Metrics Overhead** | Use appropriate collection interval |
| **Tracing Volume** | Implement sampling for high throughput |

## API Reference

### Configuration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/config` | GET | Retrieve observability configuration |
| `/observability/config` | PUT | Update observability configuration |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/stats` | GET | Get combined observability statistics |

### Audit

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/audit/events` | GET | List audit events with filters |
| `/observability/audit/stats` | GET | Get audit statistics |

### Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/metrics` | GET | Get all metrics |
| `/observability/metrics/store` | GET | Get store-specific metrics |

### Tracing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/tracing/stats` | GET | Get tracing statistics |
| `/observability/tracing/spans` | GET | List spans with pagination |

## References

### Industry Standards

| Standard | Description |
|----------|-------------|
| **OpenTelemetry** | Unified observability framework |
| **Prometheus** | Metrics collection and alerting |
| **Jaeger/Zipkin** | Distributed tracing systems |

### Related Documentation

- [Maintenance](./maintenance.md) - System maintenance and cleanup
- [Storage Tiering](./storage-tiering.md) - Data lifecycle management
- [Alerts](./alerts.md) - Alert management and notification
