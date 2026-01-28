# Plugins

The Plugins module provides an extensibility framework for adding custom validators and reporters to the Truthound Dashboard ecosystem.

## Overview

The plugin system enables users to extend platform capabilities beyond built-in functionality. Users can discover and install plugins from the local registry, or create custom validators and reporters tailored to specific organizational data quality requirements.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Custom Validators** | Define organization-specific validation rules using Python code |
| **Custom Reporters** | Create tailored report templates using Jinja2 templating |
| **Plugin Registry** | Manage installed plugins with enable/disable functionality |
| **Dependency Tracking** | Visualize plugin dependencies |

## Plugins Interface

### Statistics Dashboard

The interface displays plugin ecosystem metrics:

| Metric | Description |
|--------|-------------|
| **Installed Plugins** | Count of installed plugins |
| **Active Plugins** | Count of enabled plugins |
| **Custom Validators** | Count of custom validators |
| **Custom Reporters** | Count of custom reporters |

## Marketplace Tab

### Browsing Available Plugins

The Marketplace tab displays plugins available for installation:

| Column | Description |
|--------|-------------|
| **Name** | Plugin identifier |
| **Description** | Plugin functionality summary |
| **Type** | Plugin category |
| **Version** | Current version |
| **Rating** | Community rating |
| **Installs** | Installation count |
| **Actions** | Install, view details |

### Filtering Plugins

#### Search

Free-text search across plugin names and descriptions.

#### Type Filter

Filter by plugin category:

| Type | Description |
|------|-------------|
| **Validator** | Custom data validation logic |
| **Reporter** | Custom report generation |

> **Note**: Connector and Transformer types are reserved for future functionality.

#### Status Filter

Filter by installation status:

| Status | Description |
|--------|-------------|
| **Available** | Not installed |
| **Installed** | Installed on system |
| **Enabled** | Installed and active |
| **Disabled** | Installed but inactive |
| **Update Available** | Newer version available |
| **Error** | Plugin in error state |

### Plugin Details

Click a plugin to view detailed information:

| Section | Content |
|---------|---------|
| **Description** | Full functionality description |
| **Version** | Current version number |
| **Dependencies** | Required dependencies |
| **Author** | Plugin creator |
| **Documentation** | Usage documentation (README) |

### Installing Plugins

1. Locate the desired plugin in the Marketplace
2. Review the plugin description and dependencies
3. Click **Install**
4. Monitor installation progress
5. Plugin becomes available after installation

## Installed Tab

### Managing Installed Plugins

The Installed tab displays all installed plugins:

| Column | Description |
|--------|-------------|
| **Name** | Plugin identifier |
| **Type** | Plugin category |
| **Version** | Installed version |
| **Status** | Enabled or disabled |
| **Actions** | Enable, disable, uninstall |

### Plugin Actions

#### Enable

Activate an installed plugin:

1. Locate the disabled plugin
2. Click **Enable**
3. Plugin becomes active

#### Disable

Deactivate a plugin without uninstalling:

1. Locate the enabled plugin
2. Click **Disable**
3. Plugin becomes inactive

#### Uninstall

Remove a plugin from the system:

1. Locate the installed plugin
2. Click **Uninstall**
3. Confirm uninstallation
4. Plugin is removed

## Validators Tab

### Custom Validator Management

Create and manage custom validators:

| Column | Description |
|--------|-------------|
| **Name** | Validator identifier |
| **Description** | Validator functionality |
| **Category** | Validator category |
| **Status** | Active or inactive |
| **Actions** | Edit, delete |

### Creating Custom Validators

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

### Validator Code Structure

Custom validators implement the validation interface:

| Component | Description |
|-----------|-------------|
| **Input** | Data column or row to validate |
| **Parameters** | Configured parameter values |
| **Output** | Validation result (pass/fail/issues) |

### Validator Parameters

Define configurable parameters:

| Parameter Type | Description |
|---------------|-------------|
| **String** | Text input |
| **Number** | Numeric input |
| **Boolean** | True/false toggle |
| **Select** | Dropdown selection |
| **Column** | Column reference |
| **Column List** | Multiple column references |

### Testing Validators

Test validators before deployment:

1. Click **Test** on the validator
2. Select a test data source
3. Configure test parameters
4. Execute test
5. Review test results

### Validator Categories

| Category | Description |
|----------|-------------|
| **Schema** | Schema structure validation |
| **Completeness** | Null/missing value checks |
| **Uniqueness** | Duplicate detection |
| **Distribution** | Value range/distribution |
| **String** | String pattern validation |
| **Datetime** | Date/time validation |
| **Custom** | User-defined category |

## Reporters Tab

### Custom Reporter Management

Create and manage custom reporters:

| Column | Description |
|--------|-------------|
| **Name** | Reporter identifier |
| **Description** | Reporter functionality |
| **Format** | Output format |
| **Status** | Active or inactive |
| **Actions** | Edit, delete, preview |

### Creating Custom Reporters

1. Click **Create Reporter**
2. Configure reporter properties:
   - **Name**: Unique identifier
   - **Description**: Functionality description
   - **Format**: Output format type
   - **Template**: Report template
3. Preview the reporter
4. Save the reporter

### Reporter Templates

Define report structure and content:

| Section | Description |
|---------|-------------|
| **Header** | Report header content |
| **Summary** | Executive summary section |
| **Details** | Detailed findings section |
| **Footer** | Report footer content |

### Template Variables

Available variables for templates:

| Variable | Description |
|----------|-------------|
| `{{source_name}}` | Data source name |
| `{{validation_date}}` | Validation timestamp |
| `{{total_issues}}` | Issue count |
| `{{passed}}` | Validation passed boolean |
| `{{issues}}` | Issue list |
| `{{statistics}}` | Aggregate statistics |

### Preview Reporters

Preview reporter output:

1. Click **Preview** on the reporter
2. Select sample data
3. View rendered output
4. Adjust template as needed

## Best Practices

### Plugin Selection

| Practice | Recommendation |
|----------|----------------|
| **Review Dependencies** | Understand plugin dependencies |
| **Read Documentation** | Understand plugin functionality |
| **Test First** | Test in non-production first |

### Custom Validator Development

| Practice | Recommendation |
|----------|----------------|
| **Clear Naming** | Use descriptive validator names |
| **Documentation** | Document validator behavior |
| **Error Handling** | Handle edge cases gracefully |
| **Testing** | Thoroughly test before deployment |

### Custom Reporter Development

| Practice | Recommendation |
|----------|----------------|
| **Template Organization** | Use clear section structure |
| **Variable Usage** | Document available variables |
| **Format Consistency** | Maintain consistent styling |
| **Preview Testing** | Test with various data |

## API Reference

### Plugin Management

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

### Custom Validators

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

### Custom Reporters

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

### Plugin Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins/{id}/documentation` | GET | Get plugin documentation |
| `/plugins/{id}/documentation/render` | POST | Render documentation in format |
