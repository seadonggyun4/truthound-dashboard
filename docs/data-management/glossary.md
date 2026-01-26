# Business Glossary

The Business Glossary module provides a standardized repository for defining, managing, and governing business terminology across the organization.

## Overview

The Business Glossary establishes a common vocabulary by defining business terms with their authoritative definitions, relationships, and lifecycle status. This shared understanding bridges the gap between technical data representations and business concepts, facilitating communication between data engineers and business stakeholders.

## Glossary Interface

### Term Listing

The main Glossary page displays all business terms in a card-based layout. Each term card presents:

| Element | Description |
|---------|-------------|
| **Term Name** | The official business term identifier |
| **Definition Preview** | Truncated definition text for quick scanning |
| **Category Badge** | Classification category for the term |
| **Status Badge** | Lifecycle status indicator |
| **Owner** | Responsible party for term governance |

### Status Indicators

Terms progress through a defined lifecycle reflected by status badges:

| Status | Color | Description |
|--------|-------|-------------|
| **Draft** | Gray | Term is under development, not yet approved for use |
| **Approved** | Green | Term has been reviewed and approved for organizational use |
| **Deprecated** | Red | Term is no longer recommended, being phased out |

### Filtering Capabilities

#### Search
Free-text search across term names and definitions.

#### Category Filter
Filter by organizational category to narrow the term list.

#### Status Filter
Filter by lifecycle status (draft, approved, deprecated).

## Term Creation

### Adding a New Term

1. Click the **Add Term** button
2. Complete the term definition form:
   - **Term Name** (required): The official business term
   - **Definition** (required): Authoritative description of the term's meaning
   - **Category** (optional): Organizational classification
   - **Status** (required): Initial lifecycle status
   - **Owner** (optional): Responsible party for governance
   - **Synonyms** (optional): Alternative names for the same concept
   - **Related Terms** (optional): Associated terms in the glossary
3. Submit to create the term record

### Definition Best Practices

When crafting term definitions:

- Use clear, unambiguous language accessible to business users
- Avoid circular definitions that reference the term being defined
- Include context about when and how the term is used
- Reference authoritative sources where applicable
- Distinguish from similar or related terms

## Term Detail Interface

The Term Detail page provides comprehensive term management through a tabbed interface.

### Overview Tab

Displays fundamental term information:

- **Definition**: Complete authoritative definition
- **Category**: Organizational classification
- **Owner**: Responsible party for governance
- **Status**: Current lifecycle status
- **Related Terms Preview**: Quick view of associated terms

### Relationships Tab

Manages semantic relationships between terms:

#### Synonyms
Terms that represent the same concept with different names:

- View all synonym relationships
- Click synonym links to navigate to related terms
- Synonyms are bidirectional: if A is synonym of B, then B is synonym of A

#### Related Terms
Terms that are conceptually connected but not synonymous:

- View all related term relationships
- Click related term links to navigate
- Related term relationships indicate conceptual proximity

### History Tab

Provides complete audit trail of term modifications:

| Column | Description |
|--------|-------------|
| **Timestamp** | Date and time of the modification |
| **Field** | The attribute that was modified |
| **Old Value** | Previous value before modification |
| **New Value** | Updated value after modification |
| **Actor** | User who performed the modification |

The history tab enables:

- Compliance auditing for governance requirements
- Understanding how term definitions have evolved
- Identifying who made specific changes
- Reverting to previous definitions if needed

### Comments Tab

Provides collaborative discussion capabilities:

- View existing comments from team members
- Add new comments for discussion or clarification
- Comments include author information and timestamps
- Use comments to propose definition changes or raise questions

## Term Management Operations

### Edit Term

Modify term metadata:

1. Click the **Edit** button on the term detail page
2. Update relevant fields (definition, category, status, etc.)
3. Save changes
4. Modification is recorded in the history tab

### Delete Term

Remove a term from the glossary:

1. Click the **Delete** button
2. Confirm the deletion in the confirmation dialog
3. The term and all associated metadata are permanently removed

Note: Deleting a term removes any column mappings in the Data Catalog that reference this term.

### Deprecate Term

Mark a term as deprecated:

1. Edit the term
2. Change status to "Deprecated"
3. Save changes
4. The term remains visible but is marked as no longer recommended

## Term Relationships

### Synonym Management

Synonyms represent equivalent terms:

- **Purpose**: Accommodate varying terminology across departments
- **Behavior**: Bidirectional relationship
- **Navigation**: Click any synonym to view its detail page
- **Use Case**: "Customer" and "Client" may be synonyms in some organizations

### Related Term Management

Related terms represent conceptual connections:

- **Purpose**: Document term associations for discovery
- **Behavior**: Relationship indicates proximity, not equivalence
- **Navigation**: Click any related term to view its detail page
- **Use Case**: "Order" may be related to "Customer" and "Product"

## Integration with Data Catalog

The Business Glossary integrates with the Data Catalog through column-term mappings:

1. **Column Mapping**: Technical columns in the catalog can be mapped to glossary terms
2. **Semantic Bridge**: Mappings connect technical names (e.g., `cust_id`) to business terms (e.g., "Customer Identifier")
3. **Bidirectional Navigation**: Navigate from terms to mapped columns and vice versa
4. **Impact Analysis**: Understand which data assets are affected by term changes

## Governance Workflow

### Recommended Term Lifecycle

1. **Draft Creation**: Subject matter expert creates initial term definition
2. **Review Process**: Data governance committee reviews definition
3. **Approval**: Term is approved and status changed to "Approved"
4. **Usage**: Term is mapped to catalog columns and used in documentation
5. **Maintenance**: Periodic review ensures definitions remain current
6. **Deprecation**: Outdated terms are marked deprecated with migration guidance

### Change Management

When term definitions require modification:

1. Document the rationale in comments
2. Make the modification
3. Review the history tab to verify changes
4. Notify stakeholders of significant definition changes
5. Update any dependent documentation or mappings

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/glossary/terms` | GET | List terms with filtering options |
| `/glossary/terms` | POST | Create a new term |
| `/glossary/terms/{id}` | GET | Retrieve term details |
| `/glossary/terms/{id}` | PUT | Update term metadata |
| `/glossary/terms/{id}` | DELETE | Delete a term |
| `/glossary/terms/{id}/history` | GET | Retrieve term modification history |
| `/glossary/terms/{id}/relationships` | GET | Retrieve term relationships |
| `/glossary/categories` | GET | List available categories |
| `/glossary/categories` | POST | Create a new category |
