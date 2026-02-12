# Plugin Extensibility Framework

The Plugin Extensibility Framework provides a systematic architecture for incorporating custom validators and reporters into the Truthound Dashboard ecosystem. This module is designed to facilitate extensibility while maintaining consistency with the platform's core validation infrastructure.

## Overview

The plugin system is intended to enable users to augment platform capabilities beyond the scope of built-in functionality. Plugins may be discovered and installed from the local registry, or custom validators and reporters may be authored to address organization-specific data quality requirements.

### Principal Capabilities

| Capability | Description |
|------------|-------------|
| **Custom Validators** | Define organization-specific validation rules using Python code |
| **Custom Reporters** | Create tailored report templates using Jinja2 templating |
| **Plugin Registry** | Manage installed plugins with enable/disable functionality |
| **Dependency Tracking** | Visualize plugin dependencies |

## Plugin Interface

### Statistical Overview Panel

The interface presents aggregate metrics pertaining to the plugin ecosystem:

| Metric | Description |
|--------|-------------|
| **Installed Plugins** | Count of installed plugins |
| **Active Plugins** | Count of enabled plugins |
| **Custom Validators** | Count of custom validators |
| **Custom Reporters** | Count of custom reporters |

## Plugin Discovery and Marketplace

### Browsing Available Plugins

The Plugin Discovery and Marketplace tab presents plugins that are available for installation:

| Column | Description |
|--------|-------------|
| **Name** | Plugin identifier |
| **Description** | Plugin functionality summary |
| **Type** | Plugin category |
| **Version** | Current version |
| **Rating** | Community rating |
| **Installs** | Installation count |
| **Actions** | Install, view details |

### Filtering Mechanisms

#### Search

Free-text search is provided across plugin names and descriptions.

#### Type Filter

Plugins may be filtered by category:

| Type | Description |
|------|-------------|
| **Validator** | Custom data validation logic |
| **Reporter** | Custom report generation |

> **Note**: Connector and Transformer types are reserved for future functionality.

#### Status Filter

Plugins may be filtered by installation status:

| Status | Description |
|--------|-------------|
| **Available** | Not installed |
| **Installed** | Installed on system |
| **Enabled** | Installed and active |
| **Disabled** | Installed but inactive |
| **Update Available** | Newer version available |
| **Error** | Plugin in error state |

### Plugin Detail View

Selecting a plugin reveals the following detailed information:

| Section | Content |
|---------|---------|
| **Description** | Full functionality description |
| **Version** | Current version number |
| **Dependencies** | Required dependencies |
| **Author** | Plugin creator |
| **Documentation** | Usage documentation (README) |

### Installation Procedure

1. Locate the desired plugin in the Marketplace
2. Review the plugin description and dependencies
3. Click **Install**
4. Monitor installation progress
5. Plugin becomes available after installation

## Installed Plugins Registry

### Plugin Lifecycle Management

The Installed Plugins Registry tab enumerates all installed plugins:

| Column | Description |
|--------|-------------|
| **Name** | Plugin identifier |
| **Type** | Plugin category |
| **Version** | Installed version |
| **Status** | Enabled or disabled |
| **Actions** | Enable, disable, uninstall |

### Plugin State Transitions

#### Activation

An installed plugin may be activated as follows:

1. Locate the disabled plugin
2. Click **Enable**
3. Plugin becomes active

#### Deactivation

A plugin may be deactivated without removal from the system:

1. Locate the enabled plugin
2. Click **Disable**
3. Plugin becomes inactive

#### Removal

A plugin may be permanently removed from the system:

1. Locate the installed plugin
2. Click **Uninstall**
3. Confirm uninstallation
4. Plugin is removed

## Custom Validator Administration

### Validator Registry and Management

Custom validators are created and administered through the following interface:

| Column | Description |
|--------|-------------|
| **Name** | Validator identifier |
| **Description** | Validator functionality |
| **Category** | Validator category |
| **Status** | Active or inactive |
| **Actions** | Edit, delete |

### Validator Creation Procedure

1. Click **Create Validator**
2. Configure validator properties:
   - **Name**: Unique identifier
   - **Description**: Functionality description
   - **Category**: Classification category
   - **Severity**: Default issue severity
   - **Parameters**: Configurable parameters
   - **Code**: Validation logic
3. Test the validator
4. Save the validator

### Validator Code Architecture

Custom validators are required to implement the validation interface:

| Component | Description |
|-----------|-------------|
| **Input** | Data column or row to validate |
| **Parameters** | Configured parameter values |
| **Output** | Validation result (pass/fail/issues) |

### Validator Parameter Specification

The following configurable parameter types are supported:

| Parameter Type | Description |
|---------------|-------------|
| **String** | Text input |
| **Number** | Numeric input |
| **Boolean** | True/false toggle |
| **Select** | Dropdown selection |
| **Column** | Column reference |
| **Column List** | Multiple column references |

### Validator Verification and Testing

It is recommended that validators be tested prior to deployment:

1. Click **Test** on the validator
2. Select a test data source
3. Configure test parameters
4. Execute test
5. Review test results

### Validator Classification Taxonomy

| Category | Description |
|----------|-------------|
| **Schema** | Schema structure validation |
| **Completeness** | Null/missing value checks |
| **Uniqueness** | Duplicate detection |
| **Distribution** | Value range/distribution |
| **String** | String pattern validation |
| **Datetime** | Date/time validation |
| **Custom** | User-defined category |

## Custom Reporter Administration

### Reporter Registry and Management

Custom reporters are created and administered through the following interface:

| Column | Description |
|--------|-------------|
| **Name** | Reporter identifier |
| **Description** | Reporter functionality |
| **Format** | Output format |
| **Status** | Active or inactive |
| **Actions** | Edit, delete, preview |

### Reporter Creation Procedure

1. Click **Create Reporter**
2. Configure reporter properties:
   - **Name**: Unique identifier
   - **Description**: Functionality description
   - **Format**: Output format type
   - **Template**: Report template
3. Preview the reporter
4. Save the reporter

### Report Template Structure

The report structure and content are defined through the following sections:

| Section | Description |
|---------|-------------|
| **Header** | Report header content |
| **Summary** | Executive summary section |
| **Details** | Detailed findings section |
| **Footer** | Report footer content |

### Template Variable Reference

The following variables are made available for use within templates:

| Variable | Description |
|----------|-------------|
| `{{source_name}}` | Data source name |
| `{{validation_date}}` | Validation timestamp |
| `{{total_issues}}` | Issue count |
| `{{passed}}` | Validation passed boolean |
| `{{issues}}` | Issue list |
| `{{statistics}}` | Aggregate statistics |

### Reporter Output Preview

Reporter output may be previewed as follows:

1. Click **Preview** on the reporter
2. Select sample data
3. View rendered output
4. Adjust template as needed

## Recommended Operational Practices

### Plugin Selection Guidelines

| Practice | Recommendation |
|----------|----------------|
| **Review Dependencies** | Understand plugin dependencies |
| **Read Documentation** | Understand plugin functionality |
| **Test First** | Test in non-production first |

### Custom Validator Development Considerations

| Practice | Recommendation |
|----------|----------------|
| **Clear Naming** | Use descriptive validator names |
| **Documentation** | Document validator behavior |
| **Error Handling** | Handle edge cases gracefully |
| **Testing** | Thoroughly test before deployment |

### Custom Reporter Development Considerations

| Practice | Recommendation |
|----------|----------------|
| **Template Organization** | Use clear section structure |
| **Variable Usage** | Document available variables |
| **Format Consistency** | Maintain consistent styling |
| **Preview Testing** | Test with various data |

## API Reference

### Plugin Lifecycle Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins` | GET | List all plugins |
| `/plugins` | POST | Register a new plugin |
| `/plugins/search` | POST | Search plugins with filters |
| `/plugins/stats` | GET | Retrieve marketplace statistics |
| `/plugins/{id}` | GET | Get plugin details |
| `/plugins/{id}` | PATCH | Update plugin metadata |
| `/plugins/{id}/install` | POST | Install a plugin |
| `/plugins/{id}/uninstall` | POST | Uninstall a plugin |
| `/plugins/{id}/enable` | POST | Enable a plugin |
| `/plugins/{id}/disable` | POST | Disable a plugin |
| `/plugins/{id}/dependencies` | GET | Get plugin dependency graph |

### Custom Validator Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/validators/custom` | GET | List custom validators |
| `/validators/custom` | POST | Create custom validator |
| `/validators/custom/categories` | GET | List validator categories |
| `/validators/custom/template` | GET | Get validator code template |
| `/validators/custom/test` | POST | Test validator code |
| `/validators/custom/{id}` | GET | Get validator details |
| `/validators/custom/{id}` | PATCH | Update custom validator |
| `/validators/custom/{id}` | DELETE | Delete custom validator |

### Custom Reporter Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reporters/custom` | GET | List custom reporters |
| `/reporters/custom` | POST | Create custom reporter |
| `/reporters/custom/templates` | GET | Get reporter code templates |
| `/reporters/custom/preview` | POST | Preview reporter output |
| `/reporters/custom/{id}` | GET | Get reporter details |
| `/reporters/custom/{id}` | PATCH | Update custom reporter |
| `/reporters/custom/{id}` | DELETE | Delete custom reporter |
| `/reporters/custom/{id}/generate` | POST | Generate report |
| `/reporters/custom/{id}/download` | GET | Download generated report |

### Plugin Documentation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins/{id}/documentation` | GET | Get plugin documentation |
| `/plugins/{id}/documentation/render` | POST | Render documentation in format |
