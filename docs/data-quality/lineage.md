# Data Lineage

The Data Lineage module provides visualization and analysis of data flow relationships, enabling users to understand how data moves through systems and assess the impact of changes.

## Overview

Data lineage tracks the origin, movement, and transformation of data across systems. This module renders lineage graphs showing upstream sources and downstream consumers, with integrated anomaly visualization and multi-engine rendering support.

## Lineage Interface

### Graph Visualization

The lineage interface centers on an interactive graph visualization:

| Element | Description |
|---------|-------------|
| **Nodes** | Represent data assets — sources, transformations, and sinks |
| **Edges** | Represent data flow relationships between nodes |
| **Layout** | Hierarchical arrangement showing upstream-to-downstream flow |

### Node Types

| Type | Icon | Description |
|------|------|-------------|
| **Source** | Database icon | Origin data sources (databases, files, APIs) |
| **Transform** | Processing icon | Data transformation steps (joins, filters, aggregations) |
| **Sink** | Output icon | Final destinations (reports, exports, downstream systems) |

### Edge Types

| Type | Description |
|------|-------------|
| **derives_from** | Derived-from relationship (output depends on input) |
| **transforms_to** | Transformation output relationship |
| **joins_with** | Join relationship between data assets |
| **filters_from** | Filtered subset of source data |

## Renderer Selection

The system supports three rendering engines, each optimized for different use cases. Select a renderer from the dropdown menu at the top of the lineage page.

### Renderer Comparison

| Renderer | Technology | Best For | Node Capacity | Interactive |
|----------|-----------|----------|---------------|-------------|
| **React Flow** | React Flow library | General use, editing | Up to 500 nodes | ✅ Full |
| **Cytoscape** | Cytoscape.js (Canvas) | Large graphs, performance | 500+ nodes | ✅ Full |
| **Mermaid** | Mermaid.js (SVG) | Documentation, export | Up to 200 nodes | ⚠️ Click only |

### React Flow (Default)

The default renderer provides the richest interactive experience:

- Drag-and-drop node repositioning
- Zoom and pan navigation
- Edge routing with bezier curves
- Mini-map overview panel

### Cytoscape

A high-performance canvas-based renderer designed for large lineage graphs:

**Layout Options:**

| Layout | Description | Best For |
|--------|-------------|----------|
| **Dagre** | Hierarchical directed graph layout | Default; clear upstream/downstream flow |
| **Breadthfirst** | Breadth-first tree layout | Shallow, wide hierarchies |
| **Cose** | Compound spring embedder | Organic cluster visualization |
| **Circle** | Circular node arrangement | Identifying central nodes |
| **Grid** | Grid-aligned arrangement | Uniform spacing |
| **Concentric** | Concentric circles by degree | Highlighting connectivity |

**Controls:**

| Button | Function |
|--------|----------|
| Zoom In (+) | Increase zoom level |
| Zoom Out (−) | Decrease zoom level |
| Reset (↻) | Re-run layout algorithm and fit graph to viewport |

### Mermaid

An SVG-based renderer optimized for diagram export and documentation embedding. The Mermaid renderer exclusively uses the **simple** style for clean, readable output.

**Direction Options:**

| Direction | Code | Description |
|-----------|------|-------------|
| Left to Right | `LR` | Horizontal left-to-right flow |
| Top to Bottom | `TB` | Vertical top-to-bottom flow |
| Right to Left | `RL` | Horizontal right-to-left flow |
| Bottom to Top | `BT` | Vertical bottom-to-top flow |

**Node Click Interaction:**

Clicking a node in the Mermaid diagram opens the Node Details panel on the right side, identical to the behavior of other renderers. The system matches clicked SVG elements to lineage nodes using multiple ID-matching strategies.

## Node Details Panel

Clicking any node in the lineage graph opens a details panel on the right side of the interface.

### Panel Contents

| Section | Description |
|---------|-------------|
| **Header** | Node name and type badge |
| **Linked Source** | Link to the associated data source (if applicable) |
| **Metadata** | Additional metadata key-value pairs |
| **Connected Nodes** | List of upstream and downstream connections |
| **Impact Analysis** | Button to trigger impact analysis from this node |
| **Timestamps** | Creation and last update timestamps |

## Node Management

### Adding Nodes

1. Click the **Add Node** button
2. Configure node properties:
   - **Name**: Identifier for the node
   - **Type**: Classification (source, transform, sink)
   - **Source Reference**: Optional link to a data source
   - **Description**: Documentation text
3. Save to add the node to the graph

### Deleting Nodes

1. Select the target node
2. Click the **Delete** button in the details panel
3. Confirm deletion
4. The node and all associated edges are removed

## Impact Analysis

### Overview

Impact Analysis evaluates which nodes are affected when a selected node undergoes changes. It leverages the truthound library's `ImpactAnalyzer` for downstream traversal and the dashboard's internal graph traversal for upstream analysis.

### Initiating Impact Analysis

1. Select a node in the lineage graph
2. In the Node Details panel, click **Impact Analysis**
3. The system analyzes both upstream and downstream dependencies

### Impact Analysis Results

The results panel displays:

| Section | Description |
|---------|-------------|
| **Root Node** | The node being analyzed, with total affected count |
| **Upstream Nodes** | Nodes that feed data into the selected node |
| **Downstream Nodes** | Nodes that consume data from the selected node |
| **High Impact Warning** | Displayed when more than 5 nodes are affected |

Each affected node appears as a badge with color-coded type indicators.

### Severity Indicators

| Indicator | Condition | Description |
|-----------|-----------|-------------|
| ✅ Green check | ≤ 5 affected nodes | Low impact; changes are relatively safe |
| ⚠️ Amber warning | > 5 affected nodes | High impact; review dependencies before proceeding |

### Use Cases

**Change Impact Assessment:**
- Before modifying a table schema, identify all downstream consumers
- Before deprecating a data source, understand the blast radius
- Before changing transformation logic, verify affected outputs

**Root Cause Analysis:**
- When data quality issues are detected, trace back to the originating source
- When downstream systems report failures, identify the upstream breakpoint

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

## Export Capabilities

### Export Panel

Access the Export panel from the top-right menu to generate lineage artifacts in various formats.

### Supported Formats

| Format | Extension | Source | Description |
|--------|-----------|--------|-------------|
| **SVG** | `.svg` | All renderers | Scalable vector image; resolution-independent |
| **PNG** | `.png` | Cytoscape, React Flow | Raster image at 2× resolution |
| **Mermaid Code** | `.mmd` | Generated | Mermaid diagram source code |
| **JSON** | `.json` | API data | Raw lineage graph data |

### Export by Renderer

| Renderer | SVG | PNG | Mermaid Code | JSON |
|----------|-----|-----|-------------|------|
| **React Flow** | ✅ | ✅ (via SVG) | ✅ | ✅ |
| **Cytoscape** | ✅ (embedded) | ✅ (native) | ✅ | ✅ |
| **Mermaid** | ✅ (native) | ✅ (via SVG) | ✅ | ✅ |

**Notes on Cytoscape SVG export:** Cytoscape renders to an HTML Canvas element. SVG export wraps the high-resolution PNG output inside an `<svg>` container with an embedded `<image>` element, producing a portable SVG file suitable for documentation.

### Copy to Clipboard

- **Mermaid Code**: Copy the generated Mermaid diagram source to the clipboard
- **JSON**: Copy the raw lineage graph data as JSON

## Performance Optimization

For large lineage graphs (500+ nodes), the system provides performance optimizations:

| Technique | Description |
|-----------|-------------|
| **Clustering** | Groups related nodes to reduce visual complexity |
| **Virtualization** | Renders only visible nodes for improved frame rates |
| **Level-of-Detail** | Reduces rendered detail at lower zoom levels |
| **Canvas Rendering** | Cytoscape uses Canvas instead of DOM for better performance |

### Recommended Renderer by Graph Size

| Graph Size | Recommended Renderer |
|-----------|---------------------|
| < 100 nodes | React Flow with full detail |
| 100–500 nodes | React Flow with selective detail |
| 500–1,000 nodes | Cytoscape with Dagre layout |
| 1,000+ nodes | Cytoscape with sub-graph filtering |

## Integration with Other Modules

### Data Catalog Integration

- Lineage nodes link to catalog assets
- Impact analysis considers catalog relationships

### Anomaly Detection Integration

- Anomaly status overlaid on lineage nodes
- Correlated alerts visible in node details
- Impact propagation analysis for anomalies

### Drift Monitoring Integration

- Drift status can be visualized on lineage nodes
- Impact analysis considers drift propagation
- Root cause analysis incorporates lineage context

## Truthound Library Integration

The Data Lineage module integrates with truthound's native lineage tracking capabilities from `truthound.lineage`.

### Core Components

| Component | Module | Purpose |
|-----------|--------|---------|
| `LineageTracker` | `truthound.lineage` | Automatic lineage capture and tracking |
| `ImpactAnalyzer` | `truthound.lineage` | Impact analysis with downstream propagation |
| `OpenLineageEmitter` | `truthound.lineage` | OpenLineage standard event emission |

### Type Mapping

The dashboard maintains its own simplified node/edge types that are mapped to truthound's enum types at runtime:

**Node Types:**

| Dashboard Type | truthound `NodeType` |
|---------------|---------------------|
| `source` | `NodeType.SOURCE` |
| `transform` | `NodeType.TRANSFORMATION` |
| `sink` | `NodeType.EXTERNAL` |

**Edge Types:**

| Dashboard Type | truthound `EdgeType` |
|---------------|---------------------|
| `derives_from` | `EdgeType.DERIVED_FROM` |
| `transforms_to` | `EdgeType.TRANSFORMED_TO` |
| `joins_with` | `EdgeType.JOINED_WITH` |
| `filters_from` | `EdgeType.FILTERED_TO` |

### ImpactAnalyzer

The `ImpactAnalyzer` accepts a `LineageGraph` and performs **downstream-only** traversal to determine affected nodes.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_id` | `str` | — | ID of the node to analyze |
| `max_depth` | `int` | `-1` | Maximum traversal depth (-1 for unlimited) |
| `include_validations` | `bool` | `true` | Include validation nodes in results |

**Return Value (`ImpactResult`):**

| Field | Type | Description |
|-------|------|-------------|
| `source_node` | `LineageNode` | The starting node |
| `affected_nodes` | `tuple[AffectedNode]` | All downstream-affected nodes |
| `total_affected` | `int` | Count of affected nodes |
| `max_depth` | `int` | Maximum depth reached |
| `analysis_time_ms` | `float` | Execution time in milliseconds |

> **Note:** For upstream analysis, the dashboard uses its own SQL-based graph traversal since truthound's `ImpactAnalyzer` only provides downstream impact.

### OpenLineage Support

The module supports the [OpenLineage](https://openlineage.io/) specification (v1.0.5) for interoperability with external lineage systems. OpenLineage defines a standard event model for tracking data pipeline execution, enabling cross-platform lineage integration regardless of the orchestration framework in use.

#### Event Model

OpenLineage represents data pipeline execution as a sequence of run events. Each event captures the relationship between a **job** (a unit of computation) and **datasets** (inputs and outputs).

| Event Type | Description |
|------------|-------------|
| **RunEvent** | Records the lifecycle of a job execution (START, COMPLETE, FAIL, ABORT) |
| **DatasetEvent** | Describes datasets consumed or produced, including schema facets |
| **JobEvent** | Captures job-level metadata such as namespace, name, and custom facets |

#### Compatible Systems

Truthound Dashboard generates OpenLineage-compliant events that can be consumed by:

| System | Integration Method | Description |
|--------|-------------------|-------------|
| **Marquez** | HTTP API | Open-source metadata service with native OpenLineage support |
| **DataHub** | HTTP API | Data discovery platform with lineage ingestion |
| **Apache Atlas** | Webhook | Enterprise metadata governance and lineage |
| **Atlan** | HTTP API | Modern data catalog with OpenLineage ingestion |

### OpenLineage Export

The Export panel provides two mechanisms for delivering OpenLineage events to external systems: file download and direct endpoint emission.

#### Export Settings

All export operations share a common set of configuration parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Job Namespace** | `truthound-dashboard` | Logical grouping identifier for the exported jobs. Namespaces isolate lineage events across environments (e.g., `production`, `staging`). |
| **Job Name** | `lineage_export` | Identifier for the exported job within the namespace. Combined with the namespace, this forms a globally unique job reference. |
| **Include Schema** | Enabled | When enabled, column-level schema information is embedded as dataset facets, providing downstream consumers with structural metadata. |
| **Granular Export** | Disabled | When enabled, each transformation node generates a separate pair of START and COMPLETE events. When disabled, the entire lineage graph is represented as a single composite job. |

#### Download Mode

File-based export generates OpenLineage events as a downloadable file in one of two formats:

| Format | Extension | Structure | Use Case |
|--------|-----------|-----------|----------|
| **JSON** | `.json` | Single JSON array containing all events, formatted with indentation | Human-readable inspection, documentation, version control |
| **NDJSON** | `.ndjson` | One JSON object per line, no outer array | Streaming ingestion, log-based pipelines, large event volumes |

**Workflow:**

1. Configure export settings (namespace, job name, schema inclusion, granularity)
2. Select the desired format (JSON or NDJSON)
3. Click **Preview** to generate and inspect the events before downloading
4. Review the preview summary (event count, dataset count, job count) and the first event payload
5. Click **Download** to save the file locally

#### Emit Mode

Direct emission sends OpenLineage events to an HTTP endpoint via POST requests, suitable for real-time integration with lineage consumers.

| Parameter | Required | Description |
|-----------|----------|-------------|
| **Webhook URL** | Yes | The HTTP(S) endpoint that accepts OpenLineage events. Example: `http://localhost:5000/api/v1/lineage` for Marquez. |
| **API Key** | No | Bearer token appended to the `Authorization` header for authenticated endpoints. |
| **Batch Size** | No (default: 100) | Number of events sent per HTTP request. Larger batches reduce network overhead; smaller batches provide more granular error handling. |

The emission process sends events sequentially in batches and reports the total number of successfully transmitted events upon completion.

### OpenLineage Webhooks

Webhook configurations define persistent connections to external OpenLineage consumers. Unlike the one-time emission in Export mode, webhooks enable continuous event forwarding for ongoing lineage synchronization.

#### Webhook Management

| Operation | Description |
|-----------|-------------|
| **Add Webhook** | Register a new endpoint with name, URL, optional API key, headers, and timeout |
| **Edit Webhook** | Modify an existing webhook's configuration |
| **Delete Webhook** | Remove a webhook registration |
| **Test Webhook** | Send a test OpenLineage event to verify endpoint connectivity and measure response latency |
| **Activate / Deactivate** | Toggle a webhook between Active and Inactive states without deleting the configuration |

#### Webhook Properties

| Property | Description |
|----------|-------------|
| **Name** | Human-readable identifier for the webhook |
| **URL** | Target HTTP(S) endpoint |
| **Status** | Active (events are forwarded) or Inactive (events are not forwarded) |
| **API Key** | Optional authentication credential |
| **Headers** | Optional custom HTTP headers (key-value pairs) |
| **Timeout** | Maximum wait time for endpoint response (seconds) |

#### Connectivity Testing

The **Test** button sends a probe event to the configured endpoint and reports:

| Field | Description |
|-------|-------------|
| **Success / Failure** | Whether the endpoint accepted the event |
| **Response Time** | Round-trip latency in milliseconds |
| **Status Code** | HTTP status code returned by the endpoint |
| **Error Message** | Diagnostic information if the test fails |

Test events include a special header to distinguish them from production lineage events, allowing receiving systems to discard or flag them appropriately.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/lineage/graph` | GET | Retrieve full lineage graph (nodes + edges) |
| `/lineage/nodes` | GET | List all lineage nodes |
| `/lineage/nodes` | POST | Create a new node |
| `/lineage/nodes/{id}` | GET | Get node details |
| `/lineage/nodes/{id}` | DELETE | Delete a node |
| `/lineage/nodes/{id}/impact` | GET | Execute impact analysis |
| `/lineage/edges` | GET | List all lineage edges |
| `/lineage/edges` | POST | Create a new edge |
| `/lineage/edges/{id}` | DELETE | Delete an edge |
| `/lineage/positions` | POST | Update node positions (batch) |
| `/lineage/auto-discover` | POST | Auto-discover lineage from data sources |
| `/lineage/openlineage/export` | POST | Export lineage as OpenLineage events |
| `/lineage/openlineage/export/granular` | POST | Export with per-transformation events |
| `/lineage/openlineage/emit` | POST | Emit events to an external endpoint |
| `/lineage/openlineage/webhooks` | GET | List webhook configurations |
| `/lineage/openlineage/webhooks` | POST | Create a webhook configuration |
| `/lineage/openlineage/webhooks/{id}` | PUT | Update a webhook configuration |
| `/lineage/openlineage/webhooks/{id}` | DELETE | Delete a webhook configuration |
| `/lineage/openlineage/webhooks/test` | POST | Test webhook endpoint connectivity |

## Best Practices

### Lineage Documentation

1. **Completeness**: Ensure all data flows are documented with appropriate node types
2. **Accuracy**: Validate lineage relationships periodically using auto-discovery
3. **Maintenance**: Update lineage when systems change or data sources are added
4. **Export**: Regularly export lineage diagrams for offline documentation

### Renderer Selection Guidelines

| Scenario | Recommended Renderer |
|----------|---------------------|
| Day-to-day exploration | React Flow |
| Performance-critical large graphs | Cytoscape |
| Generating documentation | Mermaid |
| Embedding in wikis or README files | Mermaid (copy Mermaid code) |
| Sharing with stakeholders | Export as SVG or PNG |
