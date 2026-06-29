# Stage 01 — Read

**Job:** Gather current state from the blackboard and any external sources.
Produce a state packet the next stage can plan from. No mutations, no decisions.

## Inputs

- `entity_id` — which entity this run is scoped to
- `workspace_id` — the active workspace session
- *(add any other required inputs your discipline needs)*

## Process

1. Read entity base state from the blackboard (`entities` table)
2. Read any prior decisions or learnings relevant to this run
3. Read external data if needed (pull from source, write to staging table)
4. Assemble a state packet

## Outputs

A typed state packet written to the workspace and passed to `02_plan`.
See `data_packet_spec.md` for the envelope format.

```json
{
  "stage": "01_read",
  "entity_id": "<id>",
  "state": {
    "<field>": "<value>"
  },
  "data_gaps": [],
  "ready_for_plan": true
}
```

## Gate

None at this stage. Read is always safe.

## Verify

- All required fields present in the state packet
- No `null` values for required fields (flag as `data_gaps` instead)
