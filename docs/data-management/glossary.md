# Business Glossary

The Business Glossary module implements a standardized terminological repository for the definition, management, and governance of business terminology across the organization.

## Overview

The Business Glossary establishes a controlled vocabulary through the formal definition of business terms, accompanied by their authoritative descriptions, semantic relationships, and lifecycle status designations. This shared conceptual framework establishes a semantic bridge between technical data representations and business domain concepts, thereby facilitating effective discourse between data engineering practitioners and business stakeholders.

## Glossary Interface Specifications

### Term Listing

The primary Glossary page renders all registered business terms in a card-based layout. Each term card presents the following informational elements:

| Element | Description |
|---------|-------------|
| **Term Name** | The official business term identifier |
| **Definition Preview** | Truncated definition text for rapid assessment |
| **Category Badge** | Classification category assigned to the term |
| **Status Badge** | Lifecycle status indicator |
| **Owner** | Designated party responsible for term governance |

### Status Indicators

Terms are advanced through a formally defined lifecycle, as reflected by status badge designations:

| Status | Color | Description |
|--------|-------|-------------|
| **Draft** | Gray | The term is under development and has not yet been approved for organizational use |
| **Approved** | Green | The term has been reviewed and formally approved for organizational use |
| **Deprecated** | Red | The term is no longer recommended and is being systematically phased out |

### Filtering Capabilities

#### Search
Free-text search is provided across term names and definitions.

#### Category Filter
Terms may be filtered by organizational category to refine the displayed term listing.

#### Status Filter
Terms may be filtered by lifecycle status (draft, approved, deprecated).

### Category Hierarchy Breadcrumb

When terms are assigned to categories that participate in parent-child relationships, the term listing renders a breadcrumb indicating the complete category path:

```
Root Category > Parent Category > Current Category
```

This hierarchical representation enables users to ascertain the term's organizational context upon initial inspection.

## Tabs Navigation

The Glossary page is organized into two principal tabs:

| Tab | Description |
|-----|-------------|
| **Terms** | Enumerate and manage registered business terms |
| **Categories** | Administer category hierarchy with tree-based visualization |

## Term Registration

### Adding a New Term

1. Click the **Add Term** button
2. Complete the term definition form:
   - **Term Name** (required): The official business term
   - **Definition** (required): Authoritative description of the term's semantic meaning
   - **Category** (optional): Organizational classification designation
   - **Status** (required): Initial lifecycle status assignment
   - **Owner** (optional): Designated party responsible for governance
   - **Synonyms** (optional): Alternative lexical representations for the same concept
   - **Related Terms** (optional): Associated terms within the glossary
3. Submit to create the term record

### Definition Authoring Best Practices

The following guidelines should be observed when formulating term definitions:

- Clear, unambiguous language accessible to business users should be employed
- Circular definitions that reference the term being defined must be avoided
- Contextual information regarding the circumstances and manner in which the term is applied should be included
- Authoritative sources should be referenced where applicable
- Disambiguation from similar or related terms should be provided

## Term Detail Management Interface

The Term Detail page provides comprehensive term management capabilities through a tabbed interface paradigm.

### Overview Tab

The fundamental term information is displayed as follows:

- **Definition**: Complete authoritative definition
- **Category**: Organizational classification designation
- **Owner**: Designated party responsible for governance
- **Status**: Current lifecycle status
- **Related Terms Preview**: Abbreviated view of associated terms

### Relationships Tab

The Relationships tab furnishes a comprehensive interface for the management of all semantic relationship types between terms. Relationships are organized by type and rendered in a 2x2 grid layout.

#### Relationship Types

| Type | Icon | Description |
|------|------|-------------|
| **Parent** | ↑ | Broader or superordinate terms that encompass this term |
| **Child** | ↓ | Narrower or subordinate terms classified under this term |
| **Synonym** | ⇆ | Alternative lexical representations for the same concept |
| **Related** | ↔ | Conceptually associated terms without hierarchical dependency |

#### Adding Relationships

1. Click the **Add Relationship** button
2. Select the relationship type (Parent, Child, Synonym, or Related)
3. Designate the target term from the dropdown
4. Preview the relationship prior to persistence
5. Click **Save** to instantiate the relationship

#### Relationship Validation

The system enforces the following constraints:
- **Self-reference prevention**: A term is prohibited from establishing a relationship with itself
- **Duplicate prevention**: Identical relationships cannot be instantiated more than once

#### Managing Relationships

Each relationship card displays the following elements:
- Relationship type badge with color-coded designation
- Target term name (presented as a navigable hyperlink)
- Delete button for the removal of the relationship

#### Parent/Child Hierarchy

Parent and Child relationships facilitate the construction of term hierarchies:

- **Parent terms**: Broader, superordinate concepts (e.g., "Financial Metric" serves as parent of "Revenue")
- **Child terms**: More specific, subordinate concepts (e.g., "Monthly Revenue" serves as child of "Revenue")

This hierarchical structure complements the category system by establishing semantic relationships between the terms themselves.

#### Synonyms
Terms that denote the same concept through differing lexical representations:

- All synonym relationships may be viewed
- Synonym links may be navigated to access related term detail pages
- Synonyms are bidirectional in nature: if A is designated as a synonym of B, then B is correspondingly designated as a synonym of A

#### Related Terms
Terms that are conceptually associated but not semantically equivalent:

- All related term relationships may be viewed
- Related term links may be navigated to access corresponding detail pages
- Related term relationships are indicative of conceptual proximity

### History Tab

A comprehensive audit trail of term modifications is maintained:

| Column | Description |
|--------|-------------|
| **Timestamp** | Date and time at which the modification was recorded |
| **Field** | The attribute that was subject to modification |
| **Old Value** | The value prior to modification |
| **New Value** | The value subsequent to modification |
| **Actor** | The user who performed the modification |

The history tab enables the following governance functions:

- Compliance auditing in accordance with governance requirements
- Examination of how term definitions have evolved over time
- Identification of the parties responsible for specific modifications
- Reversion to previous definitions when deemed necessary

### Comments Tab

Collaborative discussion capabilities are provided:

- Existing comments from team members may be reviewed
- New comments may be contributed for discussion or clarification purposes
- Comments are annotated with author information and timestamps
- Comments may be utilized to propose definition modifications or to raise substantive questions

## Term Lifecycle Management

### Edit Term

Term metadata may be modified as follows:

1. Click the **Edit** button on the term detail page
2. Update the relevant fields (definition, category, status, etc.)
3. Persist the changes
4. The modification is recorded in the history tab

### Delete Term

A term may be removed from the glossary through the following procedure:

1. Click the **Delete** button
2. Confirm the deletion in the confirmation dialog
3. The term and all associated metadata are permanently removed

Note: Deletion of a term results in the removal of any column mappings in the Data Catalog that reference the affected term.

### Deprecate Term

A term may be designated as deprecated through the following procedure:

1. Edit the term
2. Change the status to "Deprecated"
3. Persist the changes
4. The term remains visible but is formally designated as no longer recommended for use

## Semantic Relationship Management

### Synonym Management

Synonyms represent semantically equivalent terms:

- **Purpose**: Accommodate varying terminological conventions across organizational departments
- **Behavior**: Bidirectional relationship
- **Navigation**: Any synonym may be selected to access its detail page
- **Use Case**: "Customer" and "Client" may be designated as synonyms within certain organizational contexts

### Related Term Management

Related terms represent conceptual associations:

- **Purpose**: Document inter-term associations for purposes of discovery and navigation
- **Behavior**: The relationship is indicative of semantic proximity, not equivalence
- **Navigation**: Any related term may be selected to access its detail page
- **Use Case**: "Order" may be associated with "Customer" and "Product" as related terms

## Hierarchical Category Management

The Categories tab provides a dedicated interface for the administration of the category hierarchy.

### Category Tree Visualization

Categories are rendered in an expandable tree structure:

- **Folder icons** denote category nodes
- **Expand/Collapse controls** govern the visibility of child categories
- **Term count badges** indicate the number of terms assigned to each category
- **Subcategory count badges** indicate the number of child categories

### Tree Controls

| Control | Action |
|---------|--------|
| **Expand** | Display all categories simultaneously |
| **Collapse** | Conceal all nested categories |
| **Add Category** | Instantiate a new category (root or child level) |

### Category Operations

#### Creating Categories

1. Click the **Add Category** button
2. Enter the category name (required)
3. Provide an optional description
4. Select a parent category (or designate as "No parent" for root-level placement)
5. Click **Save**

#### Editing Categories

1. Hover over a category row to reveal the action menu
2. Click the menu icon (⋮)
3. Select **Edit Category**
4. Modify the name, description, or parent designation
5. Click **Save**

Note: The system enforces prevention of circular references when modifying parent category assignments.

#### Deleting Categories

1. Access the action menu for the target category
2. Select **Delete Category**
3. Confirm in the dialog

**Warning**: Deletion of a category will result in all terms within that category being reclassified as uncategorized. Child categories must be addressed through separate administrative action.

#### Creating Subcategories

To instantiate a category as a child of an existing category:

1. Hover over the intended parent category
2. Click the action menu (⋮)
3. Select **Add Category**
4. The parent is automatically pre-selected
5. Enter the subcategory details and persist

### Hierarchical Organization

Categories support unlimited nesting depth:

```
Business Terms
├── Financial Metrics
│   ├── Revenue Metrics
│   └── Cost Metrics
├── Customer Terms
│   ├── Demographics
│   └── Behavior
└── Product Terms
    ├── Catalog
    └── Pricing
```

Each level within the hierarchy serves to organize terms into logically coherent groupings that reflect the organization's taxonomic structure.

## Data Catalog Integration Architecture

The Business Glossary is integrated with the Data Catalog through column-to-term mapping mechanisms:

1. **Column Mapping**: Technical columns within the catalog may be mapped to corresponding glossary terms
2. **Semantic Bridge**: Mappings establish a formal correspondence between technical identifiers (e.g., `cust_id`) and their business term counterparts (e.g., "Customer Identifier")
3. **Bidirectional Navigation**: Navigation is supported from terms to their mapped columns and conversely
4. **Impact Analysis**: The downstream effects upon data assets resulting from term modifications may be systematically assessed

## Governance Workflow Methodology

### Recommended Term Lifecycle

1. **Draft Creation**: A subject matter expert authors the initial term definition
2. **Review Process**: The data governance committee conducts a formal review of the definition
3. **Approval**: The term is approved and its status is transitioned to "Approved"
4. **Usage**: The term is mapped to catalog columns and incorporated into organizational documentation
5. **Maintenance**: Periodic reviews are conducted to ensure that definitions remain current and accurate
6. **Deprecation**: Outdated terms are designated as deprecated, accompanied by migration guidance

### Change Management

When term definitions necessitate modification, the following procedure should be observed:

1. Document the rationale in the comments section
2. Execute the modification
3. Review the history tab to verify that changes have been recorded accurately
4. Notify relevant stakeholders of significant definition changes
5. Update any dependent documentation or column mappings accordingly

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/glossary/terms` | GET | List terms with filtering options |
| `/glossary/terms` | POST | Create a new term |
| `/glossary/terms/{id}` | GET | Retrieve term details |
| `/glossary/terms/{id}` | PUT | Update term metadata |
| `/glossary/terms/{id}` | DELETE | Delete a term |
| `/glossary/terms/{id}/history` | GET | Retrieve term modification history |
| `/glossary/terms/{id}/relationships` | GET | List term relationships |
| `/glossary/relationships` | POST | Create term relationship |
| `/glossary/relationships/{id}` | DELETE | Remove term relationship |
| `/glossary/categories` | GET | List available categories |
| `/glossary/categories` | POST | Create a new category |
| `/glossary/categories/{id}` | GET | Retrieve category details |
| `/glossary/categories/{id}` | PUT | Update category |
| `/glossary/categories/{id}` | DELETE | Delete category |

### Term Registration Request

```json
{
  "name": "Customer Lifetime Value",
  "definition": "The total revenue expected from a customer over their entire relationship with the company.",
  "category_id": "finance-terms-uuid",
  "status": "draft",
  "owner_id": "analytics-team"
}
```

### Term Update Request

```json
{
  "definition": "Updated definition text...",
  "status": "approved",
  "category_id": "new-category-uuid"
}
```

### Term Status Values

| Status | Description |
|--------|-------------|
| `draft` | The term is under development and has not yet been approved |
| `approved` | The term has been reviewed and formally approved for use |
| `deprecated` | The term is being phased out; new usage should be avoided |

### Category with Hierarchy

Categories support parent-child relationships for hierarchical organization:

```json
{
  "name": "Financial Metrics",
  "description": "Terms related to financial performance measurement",
  "parent_id": "business-metrics-uuid"
}
```

The `full_path` field in category responses conveys the complete hierarchy path (e.g., "Business Metrics > Financial Metrics").

### Relationship Creation Request

```json
{
  "source_term_id": "term-uuid-1",
  "target_term_id": "term-uuid-2",
  "relationship_type": "parent"
}
```

### Relationship Types

| Type | Description |
|------|-------------|
| `synonym` | Terms that denote the same concept |
| `related` | Terms that are conceptually associated |
| `parent` | The target term represents a broader concept |
| `child` | The target term represents a narrower concept |
