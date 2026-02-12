# Observability

The Observability module provides comprehensive system monitoring capabilities through three interconnected pillars: Audit Logging, Metrics Collection, and Distributed Tracing. This facility leverages the observability infrastructure native to truthound's store layer, thereby furnishing enterprise-grade visibility into the operational behavior of the system.

## General Overview

Observability within contemporary data quality systems transcends the scope of traditional monitoring by affording deep insight into system behavior, performance characteristics, and operational patterns. The Truthound Dashboard implements the three canonical pillars of observability, enabling administrators to ascertain not merely *what* transpired, but *why* it transpired.

### The Three Pillars of Observability

| Pillar | Purpose | Key Questions Answered |
|--------|---------|------------------------|
| **Audit Logging** | Immutable record of all operations | Who did what, when, and what was the outcome? |
| **Metrics** | Quantitative measurements over time | How is the system performing? What are the trends? |
| **Tracing** | Request flow across components | Where are bottlenecks? How do operations flow? |

## Theoretical Foundations

### Audit Logging

Audit logging furnishes a chronological, immutable record of all significant operations performed within the system. In contrast to application logs, which are designed primarily for debugging purposes, audit logs are intended to serve compliance, security, and operational analysis objectives.

#### Audit Event Model

Each audit event captures contextual information in accordance with the W5 principle:

| Dimension | Field | Description |
|-----------|-------|-------------|
| **Who** | `user_id`, `session_id` | Identity of the actor |
| **What** | `event_type`, `store_type` | Operation performed |
| **When** | `timestamp` | Precise occurrence time |
| **Where** | `store_id`, `item_id` | Target of the operation |
| **Why/Result** | `status`, `error_message` | Outcome and context |

#### Event Type Taxonomy

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

Metrics provide quantitative measurements that facilitate trend analysis, capacity planning, and performance optimization. The system collects four distinct metric types in accordance with the RED and USE methodologies.

#### Metric Type Definitions

| Type | Description | Example |
|------|-------------|---------|
| **Counter** | Monotonically increasing value | Total operations, errors |
| **Gauge** | Point-in-time measurement | Active connections, cache size |
| **Histogram** | Distribution of values | Request latency distribution |
| **Summary** | Statistical summary with quantiles | Response time percentiles |

#### Store-Level Metrics

| Metric Category | Metrics | Purpose |
|-----------------|---------|---------|
| **Operations** | operations_total, operations_by_type | Throughput analysis |
| **I/O** | bytes_read_total, bytes_written_total | Data transfer volume |
| **Connections** | active_connections | Resource utilization |
| **Cache** | cache_hits, cache_misses, cache_hit_rate | Cache effectiveness |
| **Errors** | errors_total, errors_by_type | Reliability analysis |
| **Latency** | avg_operation_duration_ms | Performance tracking |

#### Cache Hit Rate Interpretation

The cache hit rate is regarded as a critical indicator for evaluating system efficiency:

| Hit Rate | Interpretation | Recommended Action |
|----------|----------------|-------------------|
| **> 90%** | Excellent | Maintain current configuration |
| **70-90%** | Good | Monitor for degradation |
| **50-70%** | Acceptable | Consider cache size increase |
| **< 50%** | Poor | Review access patterns, increase cache |

### Distributed Tracing

Distributed tracing provides visibility into the flow of requests across system components, thereby enabling the identification of latency bottlenecks and failure points within the execution path.

#### Fundamental Tracing Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | End-to-end journey of a request |
| **Span** | Single unit of work within a trace |
| **Context** | Propagated metadata (trace_id, span_id) |
| **Parent Span** | The span that initiated the current span |

#### Span Classification (SpanKind)

| Kind | Description | Use Case |
|------|-------------|----------|
| **Internal** | Internal operation | Business logic processing |
| **Server** | Server-side handler | API endpoint processing |
| **Client** | Client-side request | External service calls |
| **Producer** | Message producer | Async message sending |
| **Consumer** | Message consumer | Async message processing |

## Observability Interface Specification

The Observability page presents a unified view organized into five distinct tabs, each of which is described in the subsections that follow.

### 1. Overview Tab

This tab displays key summary statistics drawn from all three observability pillars:

| Card | Metrics | Purpose |
|------|---------|---------|
| **Total Events** | Audit event count | Volume indicator |
| **Events Today** | Today's event count | Current activity |
| **Error Rate** | Failure percentage | System health |
| **Cache Hit Rate** | Cache effectiveness | Performance indicator |

### 2. Audit Tab

This tab provides audit event exploration with comprehensive filtering capabilities.

#### Available Filter Options

| Filter | Description |
|--------|-------------|
| **Event Type** | Filter by specific operation type |
| **Status** | Filter by outcome (success, failure, partial, denied) |
| **Time Range** | Filter by start and end time |
| **Item ID** | Filter by specific data item |

#### Audit Table Column Definitions

| Column | Description |
|--------|-------------|
| **Event ID** | Unique identifier |
| **Type** | Operation type |
| **Timestamp** | When the event occurred |
| **Status** | Operation outcome |
| **Store** | Target store type |
| **Duration** | Operation duration in milliseconds |

### 3. Metrics Tab

This tab displays store-level metrics, organized by category as detailed below.

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

This tab displays distributed tracing statistics when tracing has been enabled in the system configuration.

| Metric | Description |
|--------|-------------|
| **Total Traces** | Number of complete traces |
| **Total Spans** | Number of individual spans |
| **Avg Trace Duration** | Average end-to-end latency |
| **Traces Today** | Today's trace count |
| **Error Rate** | Percentage of failed spans |
| **By Service** | Breakdown by service name |

### 5. Configuration Tab

This tab enables the configuration of observability features through the following parameters.

#### Configuration Parameters

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

## Data Privacy and Field-Level Redaction

The observability system incorporates field-level redaction mechanisms to ensure that sensitive data is appropriately protected within audit logs.

### Redaction Configuration

The following field types may be configured for automatic redaction:

| Field Type | Example Fields | Redaction Behavior |
|------------|----------------|-------------------|
| **Authentication** | password, token, api_key | Replace with `[REDACTED]` |
| **PII** | ssn, email, phone | Replace with `[REDACTED]` |
| **Financial** | credit_card, account_number | Replace with `[REDACTED]` |

### Redaction Guidelines

| Practice | Recommendation |
|----------|----------------|
| **Default Redaction** | Configure common sensitive fields globally |
| **Audit Review** | Periodically review logs for data leakage |
| **Compliance Alignment** | Match redaction to regulatory requirements |

## Recommended Operational Practices

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

## Integration with the Truthound Core Library

The Observability module is integrated with truthound's store observability infrastructure, as described in the following subsections.

### Store Manager Integration

The dashboard's `StoreManager` component provides layered observability through the following architectural stack:

| Layer | Component | Function |
|-------|-----------|----------|
| **Base** | Store | Core data operations |
| **Versioning** | VersionedStore | Change tracking |
| **Caching** | CachedStore | Performance optimization |
| **Tiering** | TieredStore | Data lifecycle management |
| **Observability** | AuditLogger, Metrics | Monitoring |

### Audit Logger

The truthound `AuditLogger` is responsible for automatically capturing:

- All store CRUD operations
- Operation timing and duration
- Success and failure outcomes
- User and session context

### Metrics Collector

The truthound metrics subsystem provides the following capabilities:

- Automatic metric instrumentation
- Prometheus-compatible metric format
- Histogram buckets for latency distribution
- Label-based metric dimensions

## Diagnostic and Troubleshooting Procedures

### Common Issues and Resolutions

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

### Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/config` | GET | Retrieve observability configuration |
| `/observability/config` | PUT | Update observability configuration |

### Statistics Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/stats` | GET | Get combined observability statistics |

### Audit Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/audit/events` | GET | List audit events with filters |
| `/observability/audit/stats` | GET | Get audit statistics |

### Metrics Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/metrics` | GET | Get all metrics |
| `/observability/metrics/store` | GET | Get store-specific metrics |

### Tracing Endpoints

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
