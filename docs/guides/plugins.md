# Plugins

## What this page covers

This guide explains how the dashboard exposes the Truthound plugin inventory without
reviving removed dashboard-native plugin authoring surfaces.

## Before you start

- Permission to read or manage plugins.
- A plugin identifier or search term for the registry entry you want to inspect.

## UI path or entry point

Open the Plugins page to browse installed and available plugin metadata, lifecycle
state, dependencies, and documentation rendering.

## Step-by-step workflow

1. Browse or search the plugin inventory.
2. Open a plugin detail view and inspect metadata, dependencies, and lifecycle state.
3. Install, enable, disable, or uninstall the plugin if your role permits it.
4. Use the documentation rendering view to understand the plugin before enabling it in
   operational workflows.

## Expected outputs

- A registry-only plugin workflow with no custom dashboard code editor or sandbox.
- Clear lifecycle actions tied to actual plugin state.

## Failure modes and troubleshooting

- If dependency resolution fails, inspect the plugin dependency graph before retrying.
- If documentation cannot be rendered, validate the plugin package metadata and
  documentation extraction support.

## Related APIs

- `GET /plugins`
- `GET /plugins/{plugin_id}`
- `POST /plugins/{plugin_id}/install`
- `POST /plugins/{plugin_id}/enable`
- `GET /plugins/{plugin_id}/dependencies`

## Next steps

Continue with [Observability](observability.md) if you are validating plugin behavior
after installation.
