# Data Catalog

The Data Catalog module implements a centralized metadata repository for managing metadata pertaining to data assets, enabling organizations to systematically document, discover, and govern their data resources through a structured taxonomic framework.

## Overview

The Data Catalog is designed to function as a metadata management layer that is positioned above the raw data sources, providing enriched contextual information including ownership attribution, quality scoring, column-level documentation, and semantic mappings to standardized business terminology.

## Catalog Interface Specifications

### Asset Grid Display

The primary Catalog view presents data assets in a responsive grid layout. Each asset card is rendered with the following elements:

| Element | Description |
|---------|-------------|
| **Asset Name** | The identifier for the data asset |
| **Asset Type Icon** | Visual indicator distinguishing tables, files, and APIs |
| **Quality Score** | Percentage-based data quality metric |
| **Column Count** | Number of columns defined in the asset |
| **Tag Count** | Number of classification tags applied |
| **Source Reference** | Link to the underlying data source |

### Quality Score Visualization

Quality scores are rendered through color-coded indicators in accordance with the following thresholds:

| Score Range | Color | Interpretation |
|-------------|-------|----------------|
| ≥ 80% | Green | High quality, minimal issues |
| 60% - 79% | Yellow | Moderate quality, attention recommended |
| < 60% | Red | Low quality, remediation required |

### Filtering Capabilities

The Catalog provides support for multi-dimensional filtering operations:

#### Search
Free-text search is supported across asset names and descriptions.

#### Asset Type Filter
Assets may be filtered by classification type:
- **Table**: Database tables and views
- **File**: File-based data sources
- **API**: API endpoint data sources

#### Source Filter
Assets may be filtered by the underlying data source to which they are linked.

## Asset Registration

### Registering a New Asset

1. The **Add Asset** button is selected
2. The asset registration form is completed with the following fields:
   - **Name** (required): Unique identifier for the asset
   - **Type** (required): Classification (table, file, or api)
   - **Source** (required): Associated data source
   - **Description** (optional): Documentation of the asset's purpose
   - **Owner** (optional): Responsible party for the asset
3. The form is submitted to persist the asset record

### Asset Types

| Type | Description | Analytical Use Cases |
|------|-------------|-----------|
| **Table** | Structured tabular data | Database tables, views, materialized views |
| **File** | File-based data assets | CSV, Parquet, JSON, Excel files |
| **API** | API-sourced data | REST endpoints, GraphQL queries |

## Asset Detail Management Interface

The Asset Detail page provides comprehensive metadata management capabilities through a tabbed interface architecture.

### Overview Tab

Fundamental asset information is displayed, including the following attributes:

- **Description**: Detailed documentation of the asset's purpose and contents
- **Owner**: Individual or team designated as responsible for data quality
- **Column Count**: Total number of defined columns
- **Tag Count**: Total number of applied classification tags
- **Quality Score**: Current quality assessment metric
- **Asset Type**: Classification badge
- **Source Reference**: Link to the underlying data source

### Columns Tab

Detailed column-level metadata is presented in the following structure:

| Column Attribute | Description |
|-----------------|-------------|
| **Column Name** | The identifier for the column |
| **Data Type** | The column's data type (string, integer, float, etc.) |
| **Primary Key** | Indicator if the column participates in the primary key |
| **Nullable** | Indicator if the column accepts NULL values |
| **Sensitivity Level** | Data classification (public, internal, confidential, restricted) |
| **Description** | Column-level documentation |
| **Mapped Term** | Associated business glossary term, if any |

#### Column-to-Term Mapping

The Catalog facilitates semantic mapping between technical column definitions and business glossary terms through the following procedure:

1. The target column is located in the Columns tab
2. The **Map to Term** button is selected
3. The appropriate business term is selected from the glossary
4. The mapping is rendered as a visual link between the column and term

To remove an existing mapping:
1. The mapped column is located
2. The **Unmap** button is selected
3. The association is dissolved

### Tags Tab

All classification tags applied to the asset are displayed as follows:

| Tag Attribute | Description |
|---------------|-------------|
| **Key** | The tag category or namespace |
| **Value** | The tag value or classification |

Tags are employed to enable flexible categorization for governance, compliance, and discovery purposes.

### Comments Tab

Collaborative annotation capabilities are provided through this interface:

- Existing comments contributed by team members may be reviewed
- New comments may be appended for discussion or documentation purposes
- Comments are annotated with author information and timestamps

## Asset Lifecycle Management Operations

### Edit Asset

Asset metadata may be modified through the following procedure:

1. The **Edit** button on the asset detail page is selected
2. Relevant fields are updated (name, description, owner, etc.)
3. Changes are persisted

### Delete Asset

An asset may be removed from the catalog as follows:

1. The **Delete** button is selected
2. The deletion is confirmed in the confirmation dialog
3. The asset and all associated metadata are permanently removed from the repository

## Business Glossary Integration Architecture

The Data Catalog is integrated with the Business Glossary to provide semantic contextualization:

- Columns may be mapped to glossary terms to establish semantic relationships
- Mapped relationships are bidirectionally navigable across both systems
- Term definitions provide business context for technical column identifiers
- Modifications to terms are propagated to and reflected in catalog mappings

## Analytical Use Cases

### Data Discovery

Practitioners seeking specific data assets are enabled to:

1. Employ free-text search to locate assets by name or description
2. Apply type-based filters to narrow results to tables, files, or APIs
3. Apply source-based filters to focus on specific systems
4. Evaluate quality scores to assess data reliability
5. Navigate to asset detail views for comprehensive metadata examination

### Data Governance

Data governance practitioners are enabled to:

1. Document data assets with descriptions and ownership attribution
2. Apply classification tags for compliance tracking and regulatory adherence
3. Establish mappings between columns and standardized business terms
4. Monitor quality scores across the entire asset portfolio
5. Utilize the comments facility for governance-related discourse

### Data Lineage Context

The Catalog provides contextual information in support of lineage analysis:

1. Assets are represented as nodes within lineage graphs
2. Column mappings inform column-level lineage tracking
3. Quality scores are utilized to indicate potential data quality issues along lineage paths

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/catalog/assets` | GET | List assets with filtering options |
| `/catalog/assets` | POST | Create a new asset |
| `/catalog/assets/{id}` | GET | Retrieve asset details |
| `/catalog/assets/{id}` | PUT | Update asset metadata |
| `/catalog/assets/{id}` | DELETE | Delete an asset |
| `/catalog/assets/{id}/columns` | GET | List asset columns |
| `/catalog/assets/{id}/columns` | POST | Add a column to asset |
| `/catalog/columns/{id}` | PUT | Update column metadata |
| `/catalog/columns/{id}` | DELETE | Delete a column |
| `/catalog/columns/{id}/term` | PUT | Map column to glossary term |
| `/catalog/columns/{id}/term` | DELETE | Remove column-term mapping |
| `/catalog/assets/{id}/tags` | GET | List asset tags |
| `/catalog/assets/{id}/tags` | POST | Add a tag to asset |
| `/catalog/tags/{id}` | DELETE | Delete a tag |

### Asset Registration Request

When registering an asset, initial columns and tags may be included in the request payload:

```json
{
  "name": "Customer Orders",
  "asset_type": "table",
  "source_id": "abc-123-def",
  "description": "All customer order records",
  "owner_id": "data-engineering-team",
  "columns": [
    {
      "name": "order_id",
      "data_type": "string",
      "is_primary_key": true,
      "is_nullable": false,
      "sensitivity_level": "internal"
    },
    {
      "name": "customer_email",
      "data_type": "string",
      "sensitivity_level": "confidential"
    }
  ],
  "tags": [
    {"tag_name": "domain", "tag_value": "sales"},
    {"tag_name": "compliance", "tag_value": "gdpr"}
  ]
}
```

### Column Sensitivity Levels

| Level | Description |
|-------|-------------|
| `public` | Non-sensitive data, can be shared freely |
| `internal` | Internal use only, not for external sharing |
| `confidential` | Sensitive data requiring access controls |
| `restricted` | Highly sensitive data with strict access requirements |
