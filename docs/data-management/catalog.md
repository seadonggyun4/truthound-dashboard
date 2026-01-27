# Data Catalog

The Data Catalog module provides a centralized repository for managing metadata about data assets, enabling organizations to document, discover, and govern their data resources systematically.

## Overview

The Data Catalog serves as a metadata management layer that sits above the raw data sources, providing enriched context including ownership information, quality scores, column-level documentation, and semantic mappings to business terminology.

## Catalog Interface

### Asset Grid Display

The main Catalog page presents data assets in a responsive grid layout. Each asset card displays:

| Element | Description |
|---------|-------------|
| **Asset Name** | The identifier for the data asset |
| **Asset Type Icon** | Visual indicator distinguishing tables, files, and APIs |
| **Quality Score** | Percentage-based data quality metric |
| **Column Count** | Number of columns defined in the asset |
| **Tag Count** | Number of classification tags applied |
| **Source Reference** | Link to the underlying data source |

### Quality Score Visualization

Quality scores employ color-coded indicators:

| Score Range | Color | Interpretation |
|-------------|-------|----------------|
| ≥ 80% | Green | High quality, minimal issues |
| 60% - 79% | Yellow | Moderate quality, attention recommended |
| < 60% | Red | Low quality, remediation required |

### Filtering Capabilities

The Catalog supports multi-dimensional filtering:

#### Search
Free-text search across asset names and descriptions.

#### Asset Type Filter
Filter by asset classification:
- **Table**: Database tables and views
- **File**: File-based data sources
- **API**: API endpoint data sources

#### Source Filter
Filter by the underlying data source to which assets are linked.

## Asset Creation

### Adding a New Asset

1. Click the **Add Asset** button
2. Complete the asset registration form:
   - **Name** (required): Unique identifier for the asset
   - **Type** (required): Classification (table, file, or api)
   - **Source** (required): Associated data source
   - **Description** (optional): Documentation of the asset's purpose
   - **Owner** (optional): Responsible party for the asset
3. Submit to create the asset record

### Asset Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| **Table** | Structured tabular data | Database tables, views, materialized views |
| **File** | File-based data assets | CSV, Parquet, JSON, Excel files |
| **API** | API-sourced data | REST endpoints, GraphQL queries |

## Asset Detail Interface

The Asset Detail page provides comprehensive metadata management through a tabbed interface.

### Overview Tab

Displays fundamental asset information:

- **Description**: Detailed documentation of the asset's purpose and contents
- **Owner**: Individual or team responsible for data quality
- **Column Count**: Total number of defined columns
- **Tag Count**: Total number of applied classification tags
- **Quality Score**: Current quality assessment metric
- **Asset Type**: Classification badge
- **Source Reference**: Link to the underlying data source

### Columns Tab

Presents detailed column-level metadata:

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

The Catalog supports semantic mapping between technical column definitions and business glossary terms:

1. Locate the target column in the Columns tab
2. Click the **Map to Term** button
3. Select the appropriate business term from the glossary
4. The mapping is displayed as a visual link between the column and term

To remove a mapping:
1. Locate the mapped column
2. Click the **Unmap** button
3. The association is removed

### Tags Tab

Displays all classification tags applied to the asset:

| Tag Attribute | Description |
|---------------|-------------|
| **Key** | The tag category or namespace |
| **Value** | The tag value or classification |

Tags enable flexible categorization for governance, compliance, and discovery purposes.

### Comments Tab

Provides collaborative annotation capabilities:

- View existing comments from team members
- Add new comments for discussion or documentation
- Comments include author information and timestamps

## Asset Management Operations

### Edit Asset

Modify asset metadata:

1. Click the **Edit** button on the asset detail page
2. Update relevant fields (name, description, owner, etc.)
3. Save changes

### Delete Asset

Remove an asset from the catalog:

1. Click the **Delete** button
2. Confirm the deletion in the confirmation dialog
3. The asset and all associated metadata are permanently removed

## Integration with Business Glossary

The Data Catalog integrates with the Business Glossary to provide semantic context:

- Columns can be mapped to glossary terms
- Mapped relationships are bidirectionally navigable
- Term definitions provide business context for technical column names
- Changes to terms are reflected in catalog mappings

## Use Cases

### Data Discovery

Users searching for specific data can:

1. Use free-text search to find assets by name or description
2. Filter by type to narrow results to tables, files, or APIs
3. Filter by source to focus on specific systems
4. Review quality scores to assess data reliability
5. Navigate to asset details for comprehensive metadata

### Data Governance

Governance practitioners can:

1. Document data assets with descriptions and ownership
2. Apply classification tags for compliance tracking
3. Map columns to standardized business terms
4. Monitor quality scores across the asset portfolio
5. Use comments for governance discussions

### Data Lineage Context

The Catalog provides context for lineage analysis:

1. Assets serve as nodes in lineage graphs
2. Column mappings inform column-level lineage tracking
3. Quality scores indicate potential data quality issues in lineage paths

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

### Asset Creation Request

When creating an asset, you can include initial columns and tags:

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
