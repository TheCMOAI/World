# Stage 03 — Execute

**Job:** Act on the approved plan. Write outcomes back to the blackboard.
This is the only stage that mutates state.

## Inputs

- Plan packet from `02_plan`
- Gate resolution (if any actions were gated)

## Process

1. Read plan packet from workspace
2. For each action: execute, capture outcome, write to blackboard
3. Log the decision and activity
4. Return a result packet

## Outputs

A result packet written to the blackboard.

```json
{
  "stage": "03_execute",
  "entity_id": "<id>",
  "workspace_id": "<id>",
  "results": [
    {
      "action_id": "<id>",
      "status": "done | failed | skipped",
      "outcome": {},
      "error": null
    }
  ],
  "summary": "<what happened in plain language>",
  "all_passed": true
}
```

## Gate

Do not execute any action flagged `requires_gate: true` unless the gate has been
resolved. Check `gates` table for the resolution before proceeding.

## Verify

After every action:
- Confirm the write landed (re-read the row, check updated_at)
- If verification fails, set `status: "failed"` and include the error
- Never claim an action succeeded you have not verified
