# Data Lineage

The Data Lineage module implements comprehensive visualization and analytical capabilities for data flow relationships, enabling practitioners to ascertain how data traverses through systems and to evaluate the implications of proposed modifications.

## Overview

Data lineage is concerned with the tracking of data provenance, movement, and transformation across heterogeneous systems. This module is responsible for rendering lineage graphs that depict upstream sources and downstream consumers, augmented with integrated anomaly visualization and multi-engine rendering support.

## Lineage Interface Specifications

### Graph Visualization

The lineage interface is centered upon an interactive graph visualization component:

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

## Rendering Engine Selection

The system accommodates three rendering engines, each of which has been optimized for distinct use cases. A renderer may be selected from the dropdown menu situated at the top of the lineage page.

### Renderer Comparison

| Renderer | Technology | Best For | Node Capacity | Interactive |
|----------|-----------|----------|---------------|-------------|
| **React Flow** | React Flow library | General use, editing | Up to 500 nodes | ✅ Full |
| **Cytoscape** | Cytoscape.js (Canvas) | Large graphs, performance | 500+ nodes | ✅ Full |
| **Mermaid** | Mermaid.js (SVG) | Documentation, export | Up to 200 nodes | ⚠️ Click only |

### React Flow (Default)

The default renderer is designed to furnish the most comprehensive interactive experience:

- Drag-and-drop node repositioning
- Zoom and pan navigation
- Edge routing with bezier curves
- Mini-map overview panel

### Cytoscape

A high-performance canvas-based renderer has been engineered for the visualization of large-scale lineage graphs:

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

An SVG-based renderer has been optimized for diagram export and documentation embedding purposes. The Mermaid renderer exclusively employs the **simple** style to ensure clean, readable output.

**Direction Options:**

| Direction | Code | Description |
|-----------|------|-------------|
| Left to Right | `LR` | Horizontal left-to-right flow |
| Top to Bottom | `TB` | Vertical top-to-bottom flow |
| Right to Left | `RL` | Horizontal right-to-left flow |
| Bottom to Top | `BT` | Vertical bottom-to-top flow |

**Node Click Interaction:**

When a node within the Mermaid diagram is clicked, the Node Details panel is opened on the right side, in a manner identical to the behavior exhibited by other renderers. The system resolves clicked SVG elements to their corresponding lineage nodes through the application of multiple ID-matching strategies.

## Node Details Panel

Selection of any node within the lineage graph results in the presentation of a details panel on the right side of the interface.

### Panel Contents

| Section | Description |
|---------|-------------|
| **Header** | Node name and type badge |
| **Linked Source** | Link to the associated data source (if applicable) |
| **Metadata** | Additional metadata key-value pairs |
| **Connected Nodes** | List of upstream and downstream connections |
| **Impact Analysis** | Button to trigger impact analysis from this node |
| **Timestamps** | Creation and last update timestamps |

## Node Lifecycle Management

### Adding Nodes

1. The **Add Node** button is to be clicked
2. Node properties are to be configured as follows:
   - **Name**: Identifier for the node
   - **Type**: Classification (source, transform, sink)
   - **Source Reference**: Optional link to a data source
   - **Description**: Documentation text
3. Upon saving, the node is appended to the graph

### Deleting Nodes

1. The target node is to be selected
2. The **Delete** button in the details panel is to be clicked
3. Deletion must be confirmed
4. The node and all associated edges are subsequently removed

## Impact Analysis Framework

### Overview

The Impact Analysis Framework is employed to evaluate which nodes are affected when a selected node undergoes modifications. It leverages the truthound library's `ImpactAnalyzer` for downstream traversal and utilizes the dashboard's internal graph traversal mechanism for upstream analysis.

### Initiating Impact Analysis

1. A node is to be selected within the lineage graph
2. Within the Node Details panel, the **Impact Analysis** button is to be clicked
3. The system subsequently analyzes both upstream and downstream dependencies

### Impact Analysis Results

The results panel is structured to display:

| Section | Description |
|---------|-------------|
| **Root Node** | The node being analyzed, with total affected count |
| **Upstream Nodes** | Nodes that feed data into the selected node |
| **Downstream Nodes** | Nodes that consume data from the selected node |
| **High Impact Warning** | Displayed when more than 5 nodes are affected |

Each affected node is rendered as a badge with color-coded type indicators.

### Severity Indicators

| Indicator | Condition | Description |
|-----------|-----------|-------------|
| ✅ Green check | ≤ 5 affected nodes | Low impact; changes are relatively safe |
| ⚠️ Amber warning | > 5 affected nodes | High impact; review dependencies before proceeding |

### Use Cases

**Change Impact Assessment:**
- Prior to modifying a table schema, all downstream consumers should be identified
- Prior to deprecating a data source, the blast radius must be understood
- Prior to altering transformation logic, affected outputs should be verified

**Root Cause Analysis:**
- When data quality issues are detected, the originating source should be traced
- When downstream systems report failures, the upstream breakpoint should be identified

## Anomaly Visualization Overlay

### Enabling Anomaly Visualization

1. The **Anomaly Overlay** toggle button is to be activated
2. Nodes are subsequently colored based on their anomaly status
3. The status filter may be utilized to highlight specific states

### Anomaly Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| **Normal** | Green | No anomalies detected |
| **Warning** | Yellow | Minor anomalies detected |
| **Critical** | Red | Significant anomalies detected |
| **Unknown** | Gray | No anomaly data available |

## Export and Serialization Capabilities

### Export Panel

The Export panel is accessible from the top-right menu and is utilized to generate lineage artifacts in various formats.

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

- **Mermaid Code**: The generated Mermaid diagram source may be copied to the clipboard
- **JSON**: The raw lineage graph data may be copied as JSON

## Performance Optimization Strategies

For large lineage graphs comprising 500 or more nodes, the system incorporates the following performance optimization strategies:

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

## Cross-Module Integration Architecture

### Data Catalog Integration

- Lineage nodes are linked to their corresponding catalog assets
- Impact analysis takes into consideration catalog relationships

### Anomaly Detection Integration

- Anomaly status is overlaid upon lineage nodes
- Correlated alerts are made visible within node details
- Impact propagation analysis is conducted for detected anomalies

### Drift Monitoring Integration

- Drift status may be visualized upon lineage nodes
- Impact analysis accounts for drift propagation
- Root cause analysis incorporates lineage context

## truthound Library Integration Architecture

The Data Lineage module is integrated with truthound's native lineage tracking capabilities as provided by `truthound.lineage`.

### Core Components

| Component | Module | Purpose |
|-----------|--------|---------|
| `LineageTracker` | `truthound.lineage` | Automatic lineage capture and tracking |
| `ImpactAnalyzer` | `truthound.lineage` | Impact analysis with downstream propagation |
| `OpenLineageEmitter` | `truthound.lineage` | OpenLineage standard event emission |

### Type Mapping

The dashboard maintains its own simplified node and edge type taxonomy, which is mapped to truthound's enumeration types at runtime:

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

The `ImpactAnalyzer` accepts a `LineageGraph` instance and performs **downstream-only** traversal to determine the set of affected nodes.

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

> **Note:** For upstream analysis, the dashboard employs its own SQL-based graph traversal, as truthound's `ImpactAnalyzer` is limited to downstream impact computation.

### OpenLineage Support

The module supports the [OpenLineage](https://openlineage.io/) specification (v1.0.5) for interoperability with external lineage systems. OpenLineage defines a standard event model for the tracking of data pipeline execution, thereby enabling cross-platform lineage integration irrespective of the orchestration framework employed.

#### Event Model

OpenLineage represents data pipeline execution as a sequence of run events. Each event captures the relationship between a **job** (a unit of computation) and **datasets** (inputs and outputs).

| Event Type | Description |
|------------|-------------|
| **RunEvent** | Records the lifecycle of a job execution (START, COMPLETE, FAIL, ABORT) |
| **DatasetEvent** | Describes datasets consumed or produced, including schema facets |
| **JobEvent** | Captures job-level metadata such as namespace, name, and custom facets |

#### Compatible Systems

Truthound Dashboard generates OpenLineage-compliant events that may be consumed by the following systems:

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

1. Export settings are to be configured (namespace, job name, schema inclusion, granularity)
2. The desired format (JSON or NDJSON) is to be selected
3. The **Preview** button is to be clicked to generate and inspect events prior to downloading
4. The preview summary (event count, dataset count, job count) and the first event payload are to be reviewed
5. The **Download** button is to be clicked to save the file locally

#### Emit Mode

Direct emission transmits OpenLineage events to an HTTP endpoint via POST requests, and is suitable for real-time integration with lineage consumers.

| Parameter | Required | Description |
|-----------|----------|-------------|
| **Webhook URL** | Yes | The HTTP(S) endpoint that accepts OpenLineage events. Example: `http://localhost:5000/api/v1/lineage` for Marquez. |
| **API Key** | No | Bearer token appended to the `Authorization` header for authenticated endpoints. |
| **Batch Size** | No (default: 100) | Number of events sent per HTTP request. Larger batches reduce network overhead; smaller batches provide more granular error handling. |

The emission process transmits events sequentially in batches and reports the total number of successfully delivered events upon completion.

### OpenLineage Webhooks

Webhook configurations define persistent connections to external OpenLineage consumers. In contrast to the one-time emission afforded by Export mode, webhooks facilitate continuous event forwarding for ongoing lineage synchronization.

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

The **Test** button transmits a probe event to the configured endpoint and reports:

| Field | Description |
|-------|-------------|
| **Success / Failure** | Whether the endpoint accepted the event |
| **Response Time** | Round-trip latency in milliseconds |
| **Status Code** | HTTP status code returned by the endpoint |
| **Error Message** | Diagnostic information if the test fails |

Test events include a special header to distinguish them from production lineage events, thereby allowing receiving systems to discard or flag them appropriately.

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

## Recommended Operational Practices

### Lineage Documentation

1. **Completeness**: It is imperative that all data flows are documented with appropriate node types
2. **Accuracy**: Lineage relationships should be validated periodically through the utilization of auto-discovery
3. **Maintenance**: Lineage must be updated when systems are modified or data sources are introduced
4. **Export**: Lineage diagrams should be exported regularly for offline documentation purposes

### Rendering Engine Selection Guidelines

| Scenario | Recommended Renderer |
|----------|---------------------|
| Day-to-day exploration | React Flow |
| Performance-critical large graphs | Cytoscape |
| Generating documentation | Mermaid |
| Embedding in wikis or README files | Mermaid (copy Mermaid code) |
| Sharing with stakeholders | Export as SVG or PNG |
