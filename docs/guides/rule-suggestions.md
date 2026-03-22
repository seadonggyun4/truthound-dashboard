# Rule Suggestions

## What this page covers

This guide explains how rule suggestion flows help operators bootstrap or refine rule
sets from profiles and other learned signals.

## Before you start

- Permission to read rules and use suggestion workflows.
- A recent profile or dataset state that represents the baseline you trust.
- Agreement on how aggressively suggestions should be promoted into active rules.

## UI path or entry point

Use the rule suggestion flow from the source or profiling context.

## Step-by-step workflow

1. Select the source or profile that should drive suggestion generation.
2. Review each suggestion with the same care you would apply to a manual rule.
3. Accept only suggestions that have a clear operational purpose.
4. Validate accepted suggestions against recent validation history.
5. Remove overly broad or redundant suggestions before they become maintenance burden.

## Expected outputs

- A curated list of suggested rules rather than blind automation.
- Faster onboarding for sources that already have stable profiles.
- Better alignment between profiles, history, and active rule definitions.

## Failure modes and troubleshooting

- If suggestions are too noisy, refine the baseline profile first.
- If a suggestion conflicts with known business rules, prefer explicit rule design over
  automated output.

## Related APIs

- `POST /rule-suggestions`
- `POST /rule-suggestions/from-profile`
- `GET /validators`
- `GET /rules`

## Next steps

Return to [Rule Management](rule-management.md) to finalize active rules.
