# Rule Management

## What this page covers

This guide covers how operators review, create, and maintain validation rules in the
dashboard without inventing dashboard-native validation semantics.

## Before you start

- Permission to read and write rules.
- A source or validation context where the rule should be applied.
- Awareness of the validator registry and rule suggestion features if you plan to start
  from an existing pattern.

## UI path or entry point

Open the rule management surface from a source or validation context, or use rule
suggestion flows when bootstrapping a new rule set.

## Step-by-step workflow

1. Inspect existing rules and validator metadata before creating a new rule.
2. Create or edit rules with the smallest set of parameters needed for the expected
   behavior.
3. Validate the rule against a source or validation result where the expected outcome is
   already known.
4. Review rule changes together with validation history instead of evaluating rules in
   isolation.
5. Remove or simplify rules that duplicate stronger suite-level controls.

## Expected outputs

- Rules that map cleanly onto supported Truthound validators.
- A smaller, more reviewable rule set instead of a dashboard-owned rule language.
- Rule definitions that can be reasoned about together with validation outputs.

## Failure modes and troubleshooting

- If a rule saves but does not affect runs, confirm that it is attached to the expected
  source or workflow.
- If rule intent is unclear, compare it with suggested rules or historical issues
  before adding new conditions.
- If operators cannot explain why a rule exists, treat that as a maintenance problem.

## Related APIs

- `GET /rules`
- `POST /rules`
- `PUT /rules/{rule_id}`
- `DELETE /rules/{rule_id}`
- `GET /validators`

## Next steps

Continue with [Rule Suggestions](rule-suggestions.md) if you want to bootstrap rules
from profiles or learned behavior.
