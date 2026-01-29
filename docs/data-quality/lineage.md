# Data Lineage

The Data Lineage module provides visualization and analysis of data flow relationships, enabling users to understand how data moves through systems and assess the impact of changes.

## Overview

Data lineage tracks the origin, movement, and transformation of data across systems. This module renders lineage graphs showing upstream sources and downstream consumers, supporting both table-level and column-level lineage tracking with integrated anomaly visualization.

## Lineage Interface

### Graph Visualization

The lineage interface centers on an interactive graph visualization:

| Element | Description |
|---------|-------------|
| **Nodes** | Represent data assets (tables, files, processes) |
| **Edges** | Represent data flow relationships between nodes |
| **Layout** | Hierarchical arrangement showing upstream to downstream flow |

### Renderer Selection

The system supports multiple rendering engines optimized for different scenarios:

| Renderer | Description | Best For |
|----------|-------------|----------|
| **React Flow** | Default interactive renderer | General use, up to 500 nodes |
| **Cytoscape** | Performance-optimized renderer | Large graphs (500+ nodes) |
| **Mermaid** | Export-focused renderer | Documentation generation |

### Performance Optimization

For large lineage graphs (500+ nodes), the system automatically applies:

- **Clustering**: Groups related nodes to reduce visual complexity
- **Virtualization**: Renders only visible nodes for performance
- **Level-of-Detail**: Reduces detail at lower zoom levels

A performance information popover displays:

- Current node count
- Rendering mode (normal/optimized)
- Threshold settings
- Manual override toggle

## Column Lineage

### Enabling Column-Level Tracking

1. Click the **Column Lineage** toggle button
2. The graph updates to show column-level relationships
3. Select viewing mode: Graph or Table

### Graph View

Column lineage in graph view displays:

- Table nodes with expandable column lists
- Column-to-column edge relationships
- Transformation annotations on edges

### Table View

Column lineage in table view displays:

| Column | Description |
|--------|-------------|
| **Source Table** | Origin table name |
| **Source Column** | Origin column name |
| **Target Table** | Destination table name |
| **Target Column** | Destination column name |
| **Transformation** | Applied transformation (if any) |

### Column-Level Impact Analysis

Click on any column to view:

- Upstream sources feeding this column
- Downstream targets consuming this column
- Transformation chain from source to target

## Anomaly Overlay

### Enabling Anomaly Visualization

1. Click the **Anomaly Overlay** toggle button
2. Nodes are colored based on anomaly status
3. Use the status filter to highlight specific states

### Anomaly Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| **Normal** | Green | No anomalies detected |
| **Warning** | Yellow | Minor anomalies detected |
| **Critical** | Red | Significant anomalies detected |
| **Unknown** | Gray | No anomaly data available |

### Status Filter

Filter nodes by anomaly status to focus on:

- All nodes
- Nodes with anomalies only
- Specific severity levels

## Node Management

### Adding Nodes

1. Click the **Add Node** button
2. Configure node properties:
   - **Name**: Identifier for the node
   - **Type**: Classification (table, file, process, etc.)
   - **Source Reference**: Optional link to data source
   - **Description**: Documentation
3. Save to add the node to the graph

### Deleting Nodes

1. Select the target node
2. Click the **Delete** button
3. Confirm deletion
4. Node and all associated edges are removed

## Impact Analysis

### Initiating Impact Analysis

1. Select a node in the lineage graph
2. Click **Impact Analysis**
3. Choose analysis direction:
   - **Downstream**: What is affected if this node changes
   - **Upstream**: What sources feed this node

### Impact Analysis Results

| Section | Content |
|---------|---------|
| **Direct Dependencies** | Immediately connected nodes |
| **Transitive Dependencies** | Full dependency chain |
| **Affected Assets** | Catalog assets impacted |
| **Risk Assessment** | Potential impact severity |

### Use Cases

**Change Impact Assessment**:
- Before modifying a table schema
- Before deprecating a data source
- Before changing transformation logic

**Root Cause Analysis**:
- When data quality issues are detected
- When downstream systems fail
- When anomalies are identified

## Export Capabilities

### Export Panel

Access the Export Panel to generate lineage documentation:

| Format | Description | Use Case |
|--------|-------------|----------|
| **Image** | PNG/SVG export | Presentations, documentation |
| **PDF** | Document export | Formal documentation |
| **Code** | Mermaid/GraphViz code | Version control, automation |

### Export Options

- **Full Graph**: Export entire lineage graph
- **Selection**: Export selected nodes and their relationships
- **Filtered**: Export nodes matching current filter criteria

## Node Interaction

### Node Click Actions

Clicking a node displays:

- Node details panel
- Associated data source link
- Column list (if table node)
- Validation status
- Last updated timestamp

### Edge Click Actions

Clicking an edge displays:

- Source and target node information
- Column mappings (if column lineage enabled)
- Transformation details
- Data flow direction

## Integration with Other Modules

### Data Catalog Integration

- Lineage nodes link to catalog assets
- Column lineage maps to catalog column metadata
- Impact analysis considers catalog relationships

### Anomaly Detection Integration

- Anomaly status overlaid on lineage nodes
- Correlated alerts visible in node details
- Impact propagation analysis for anomalies

### Drift Monitoring Integration

- Drift status can be visualized on lineage nodes
- Impact analysis considers drift propagation
- Root cause analysis incorporates lineage context

## Truthound Integration

The Data Lineage module leverages truthound's native lineage tracking capabilities from `truthound.lineage`:

### Core Components

| Component | Module | Purpose |
|-----------|--------|---------|
| LineageTracker | `truthound.lineage.LineageTracker` | Automatic lineage capture and tracking |
| ImpactAnalyzer | `truthound.lineage.ImpactAnalyzer` | Impact analysis with propagation |
| OpenLineage | `truthound.lineage.OpenLineageEmitter` | OpenLineage standard event emission |

### LineageTracker

The `LineageTracker` provides automatic lineage capture for data operations:

| Feature | Description |
|---------|-------------|
| Auto-tracking | Automatically captures read/write operations |
| Schema tracking | Records schema changes with lineage events |
| Operation context | Captures transformation metadata |
| Graph building | Constructs complete lineage graphs |

Configuration options (`LineageConfig`):

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `track_column_level` | `bool` | Enable column-level lineage tracking | `true` |
| `track_row_level` | `bool` | Enable row-level lineage tracking (expensive) | `false` |
| `store_samples` | `bool` | Persist data samples alongside lineage events | `false` |
| `max_history` | `int` | Maximum number of operations retained in history | `100` |
| `auto_track` | `bool` | Automatically capture read/write operations | `true` |
| `persist_path` | `str \| None` | File system path for automatic lineage persistence | `null` |
| `metadata` | `dict` | User-defined metadata attached to lineage sessions | `{}` |

### ImpactAnalyzer

The `ImpactAnalyzer` provides sophisticated impact analysis capabilities:

| Analysis Type | Description |
|---------------|-------------|
| Downstream Impact | What entities are affected by changes |
| Upstream Lineage | What sources feed an entity |
| Change Propagation | How changes cascade through the graph |
| Risk Assessment | Severity scoring for impacted entities |

### OpenLineage Support

The module supports the OpenLineage standard for lineage interoperability:

| Event Type | Description |
|------------|-------------|
| RunEvent | Job execution start/complete/fail |
| DatasetEvent | Dataset read/write operations |
| JobEvent | Job metadata and facets |

This enables integration with external lineage systems like Marquez, Datahub, and Apache Atlas.

## Best Practices

### Lineage Documentation

1. **Completeness**: Ensure all data flows are documented
2. **Accuracy**: Validate lineage relationships periodically
3. **Granularity**: Document column-level lineage for critical paths
4. **Maintenance**: Update lineage when systems change

### Performance Considerations

| Graph Size | Recommended Approach |
|-----------|---------------------|
| < 100 nodes | React Flow with full detail |
| 100-500 nodes | React Flow with selective detail |
| 500+ nodes | Cytoscape with clustering |
| 1000+ nodes | Consider sub-graph analysis |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/lineage/graph` | GET | Retrieve lineage graph |
| `/lineage/nodes` | POST | Create a new node |
| `/lineage/nodes/{id}` | DELETE | Delete a node |
| `/lineage/nodes/{id}/impact-analysis` | POST | Execute impact analysis |
| `/lineage/nodes/{id}/columns` | GET | Retrieve column lineage |
| `/lineage/edges/{id}/column-mappings` | GET | Retrieve column mappings |
| `/lineage/columns/impact` | GET | Column-level impact analysis |
