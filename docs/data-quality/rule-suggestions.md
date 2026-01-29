# Rule Suggestions

The Rule Suggestions module provides automated generation of validation rules by analyzing the statistical profile of a data source. This capability reduces the manual effort required to define comprehensive validation configurations and ensures that rules are empirically grounded in observed data characteristics.

## Overview

Rule suggestion operates as a profile-driven inference engine. The system examines column-level statistics—including null ratios, uniqueness measures, value distributions, and detected patterns—to propose validation rules with associated confidence scores. Users review, adjust, and selectively apply the generated rules to their data sources.

## Generation Workflow

### Initiating Rule Generation

1. Navigate to the **Profile** page for a data source
2. Ensure that at least one profiling result exists (run **Run Profile** if necessary)
3. Click the **Suggest Rules** button in the page header
4. The Rule Suggestion dialog opens and automatically generates an initial set of rules using default parameters

### Generation Settings

The **Settings** tab within the dialog provides fine-grained control over the generation process:

| Parameter | Type | Description |
|-----------|------|-------------|
| **Strictness** | `low` / `medium` / `high` | Controls the threshold sensitivity for rule generation. Higher strictness produces more restrictive rules |
| **Preset** | `none` / predefined sets | Applies a predefined rule template optimized for specific use cases |
| **Minimum Confidence** | `0–100%` | Excludes rules whose confidence score falls below this threshold |
| **Categories** | Multi-select | Restricts generation to specific rule categories (schema, completeness, uniqueness, distribution, stats, pattern) |

After adjusting settings, click **Generate Rules** to regenerate the entire suggestion set with the updated parameters. Each generation replaces the previous suggestion list in its entirety; rules are not incrementally appended.

### API Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sources/{id}/rules/suggest` | Generate rule suggestions based on the source's profile |

Request body parameters correspond to the dialog settings:

```json
{
  "strictness": "medium",
  "min_confidence": 0.5,
  "preset": "none",
  "include_categories": ["completeness", "uniqueness", "distribution"]
}
```

## Suggestion Review

### Suggestions Tab

Generated rules are displayed as a filterable list in the **Suggestions** tab:

| Element | Description |
|---------|-------------|
| **Validator Name** | The specific validator to be applied (e.g., `null_check`, `range_check`) |
| **Column** | Target column for column-level rules |
| **Category** | Classification (completeness, uniqueness, distribution, schema, stats, pattern) |
| **Confidence** | Numerical score (0.0–1.0) indicating the statistical confidence of the suggestion |
| **Reason** | Human-readable explanation of why the rule was suggested |

### Automatic Pre-Selection

Upon generation, rules with a confidence score of **0.85 or higher** are automatically selected for application. This behavior is designed to streamline the review process by pre-selecting rules that exhibit strong statistical support. Users may manually adjust the selection before applying.

When no suggestions are present (e.g., prior to generation or during loading), the selection state is cleared and the **Apply Rules** button is disabled.

### Filtering and Search

The suggestion list supports:

- **Text search**: Filters by validator name, column name, or reason text
- **Category filter**: Restricts the visible list to a specific rule category

## Applying Rules

1. Review and adjust the selection checkboxes in the Suggestions tab
2. Click **Apply Rules (N)** where N reflects the current selection count
3. The selected rules are submitted to the backend for persistent association with the data source
4. Applied rules become part of the source's active validation configuration

The Apply button is disabled when no rules are selected (`selectedIds.size === 0`).

## Export Capabilities

Selected rules can be exported in multiple formats for external use:

| Format | Description |
|--------|-------------|
| **YAML** | Structured configuration suitable for version control |
| **JSON** | Machine-readable format for programmatic consumption |

Export and clipboard copy operations are available only when at least one rule is selected.

## Integration with Profiling

Rule suggestion depends on prior profiling data. The quality and comprehensiveness of suggested rules is directly proportional to the richness of the underlying profile. Advanced profiling options—such as pattern detection, distribution analysis, and correlation computation—yield more diverse and precise rule suggestions.

For optimal results, consider running advanced profiling with the following configuration before generating rules:

| Setting | Recommended Value | Impact |
|---------|-------------------|--------|
| `include_patterns` | `true` | Enables pattern-based rule suggestions (email, phone, UUID) |
| `include_distributions` | `true` | Enables distribution-based range and outlier rules |
| `include_correlations` | `true` | Enables cross-column relationship rules |
| `top_n_values` | `20` | Provides richer categorical value analysis |
