# Stage 02 — Plan

**Job:** Read the state packet from `01_read` and produce a typed plan.
No mutations. No side effects. The plan is what gets approved before execution.

## Inputs

- State packet from `01_read`
- Any operator-supplied constraints or directives

## Process

1. Read state packet from workspace
2. Apply domain knowledge from `references/` to produce recommendations
3. Produce a typed plan packet with proposed actions
4. If a gate is required, surface it before returning

## Outputs

A typed plan packet written to the workspace and passed to `03_execute`.

```json
{
  "stage": "02_plan",
  "entity_id": "<id>",
  "workspace_id": "<id>",
  "plan": {
    "summary": "<one sentence>",
    "actions": [
      {
        "id": "<action_id>",
        "type": "<action_type>",
        "description": "<what this action does>",
        "reversible": true,
        "requires_gate": false,
        "payload": {}
      }
    ]
  },
  "ready_for_execute": true
}
```

## Gate

Surface a gate before returning if any proposed action:
- Is irreversible
- Affects external systems (APIs, sends messages, publishes)
- Involves spend or resource allocation
- Is ambiguous in its target

## Verify

- Every action has a type, description, and reversible flag
- All gated actions are flagged before execution stage receives the packet
