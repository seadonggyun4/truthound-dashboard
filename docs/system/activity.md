# Activity Feed

The Activity Feed provides a chronological timeline of system events and user actions, enabling audit trail visibility and operational awareness across the platform.

## Conceptual Overview

The Activity Feed aggregates events from glossary term management, catalog asset operations, and collaboration activities into a unified timeline. This centralized view is designed to support compliance auditing, change tracking, and operational monitoring by consolidating disparate event streams into a single, coherent chronological record.

## User Interface and Presentation

### Chronological Timeline Rendering

The Activity page presents events in reverse chronological order. Each entry within the timeline is composed of the following structural elements:

| Element | Description |
|---------|-------------|
| **Timestamp** | When the activity occurred |
| **Actor** | User or system component that performed the action |
| **Action** | Type of activity performed |
| **Resource** | Entity affected by the activity |
| **Details** | Additional context about the activity |

### Taxonomy of Activity Types

All recorded activities are classified according to the following typological categories:

| Activity Type | Description |
|--------------|-------------|
| **Create** | New resource was created |
| **Update** | Existing resource was modified |
| **Delete** | Resource was removed |
| **Comment** | Comment was added to a resource |
| **Status Change** | Resource status was modified |
| **Relationship Change** | Resource relationships were modified |

## Filtering and Query Mechanisms

### Resource Type Filtering

Activities may be filtered by the type of resource affected. The following resource type classifications are supported:

| Resource Type | Description |
|--------------|-------------|
| **Term** | Business glossary term activities |
| **Asset** | Data catalog asset activities |
| **Column** | Column metadata activities |

### Application of Filters

The filtering workflow is executed through the following procedure:

1. Click the **Resource Type** filter dropdown
2. Select the desired resource type
3. Activity feed updates to show matching events
4. Clear filter to view all activities

## Activity Record Specification

### Record Schema and Field Definitions

Each discrete activity record is persisted with the following set of fields:

| Field | Description |
|-------|-------------|
| **ID** | Unique activity identifier |
| **Resource Type** | Type of affected resource |
| **Resource ID** | Identifier of affected resource |
| **Resource Name** | Human-readable resource name |
| **Action** | Activity type (create, update, delete) |
| **Actor** | User who performed the action |
| **Changes** | Detailed change information (for updates) |
| **Timestamp** | When the activity occurred |

### Granular Change Documentation

For activities classified as updates, supplementary change details are recorded. Each modification is represented by the following fields:

| Field | Description |
|-------|-------------|
| **Field Name** | Which attribute was modified |
| **Old Value** | Previous value before change |
| **New Value** | Updated value after change |

## Pagination and Progressive Data Retrieval

### Data Loading Strategy

The Activity Feed employs a paginated retrieval model to ensure acceptable performance characteristics under high-volume conditions:

1. Initial load displays recent activities
2. Click **Load More** to retrieve additional activities
3. Activities continue loading in batches
4. Scroll position is preserved during loading

### Pagination Configuration Parameters

| Parameter | Description |
|-----------|-------------|
| **Skip** | Number of activities to skip |
| **Limit** | Number of activities per batch |

## Representative Use Cases

### Regulatory Audit Compliance

The Activity Feed may be utilized to satisfy regulatory change-tracking requirements through the following methodology:

1. Filter by relevant resource type
2. Review activities within audit period
3. Identify all modifications and actors
4. Export activity data for audit documentation

### Forensic Change Investigation

In circumstances where unexpected or unauthorized modifications are suspected, the following investigative procedure is recommended:

1. Identify the timeframe of concern
2. Filter activities to narrow scope
3. Trace modifications to specific actors
4. Review change details for context

### Collaborative Awareness and Team Coordination

The Activity Feed serves as a mechanism for maintaining situational awareness of team operations:

1. View recent activities across resources
2. Identify active areas of work
3. Review comments and discussions
4. Stay informed of colleague contributions

## Event Source Classification

### Glossary-Originated Activities

The following activities are generated as a consequence of glossary management operations:

| Action | Description |
|--------|-------------|
| **Term Created** | New business term added |
| **Term Updated** | Term definition or metadata modified |
| **Term Deleted** | Term removed from glossary |
| **Status Changed** | Term lifecycle status modified |
| **Relationship Added** | Synonym or related term linked |
| **Relationship Removed** | Term relationship unlinked |

### Catalog-Originated Activities

The following activities are generated as a consequence of data catalog operations:

| Action | Description |
|--------|-------------|
| **Asset Created** | New data asset registered |
| **Asset Updated** | Asset metadata modified |
| **Asset Deleted** | Asset removed from catalog |
| **Column Added** | New column defined |
| **Column Updated** | Column metadata modified |
| **Column Mapped** | Column linked to glossary term |
| **Column Unmapped** | Column-term link removed |
| **Tag Added** | Classification tag applied |
| **Tag Removed** | Classification tag removed |

### Collaboration-Originated Activities

The following activities are generated through the use of collaborative annotation features:

| Action | Description |
|--------|-------------|
| **Comment Added** | New comment posted |
| **Comment Updated** | Existing comment modified |
| **Comment Deleted** | Comment removed |

## Data Retention and Lifecycle Management

### Retention Policy

Activity records are retained in accordance with the system's configured retention policies:

- Default retention period applies to all activities
- Retention can be configured in Maintenance settings
- Older activities are purged during maintenance cycles

### Archival Procedures

For organizations subject to long-term audit retention requirements, the following archival procedure is recommended:

1. Export activity data before retention period expires
2. Store exports in external archive system
3. Reference archived data for historical audits

## Cross-Module Integration

### Glossary Module Integration

- Term activities link to glossary term detail pages
- Click resource name to navigate to the term
- View full term history in the term detail History tab

### Catalog Module Integration

- Asset activities link to catalog asset detail pages
- Click resource name to navigate to the asset
- View asset-specific activities in asset context

### Notification Subsystem Integration

Notifications may be configured in conjunction with specific activity types to facilitate proactive operational awareness:

- Alert on critical resource modifications
- Notify owners when their resources change
- Integrate with external audit systems

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/activities` | GET | List activities with filtering |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| **resource_type** | string | Filter by resource type |
| **skip** | integer | Number of records to skip |
| **limit** | integer | Maximum records to return |
