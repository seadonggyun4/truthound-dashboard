# Privacy Scan and Mask

## What this page covers

This guide covers the privacy workflow in the dashboard: scanning for sensitive data,
reviewing findings, and creating masked outputs where appropriate.

## Before you start

- A readable source.
- Permission to run scans or masking operations.
- Agreement on the masking policy you want to apply to the dataset.

## UI path or entry point

Start from the privacy or source context and run a scan first. Masking should usually
be driven by the scan result rather than started blindly.

## Step-by-step workflow

1. Run a privacy scan against the target source.
2. Review the detected sensitive fields and confidence levels.
3. Decide which fields should be masked and which policy should apply.
4. Run the masking operation.
5. Review the generated masked output or result details before using it downstream.

## Expected outputs

- A scan record that describes detected sensitive data.
- A masking result that documents which fields were transformed.
- A repeatable workflow that can be referenced in operations runbooks.

## Failure modes and troubleshooting

- If the scan finds too much or too little, inspect the scan scope and the current data
  characteristics before changing masking policy.
- If masking fails, validate the source connectivity and output permissions first.

## Related APIs

- `POST /scans`
- `GET /scans/{scan_id}`
- `POST /masks`
- `GET /masks/{mask_id}`

## Next steps

Continue with [Reports and Data Docs](reports-and-datadocs.md) if you need a shareable
artifact after a privacy workflow.
