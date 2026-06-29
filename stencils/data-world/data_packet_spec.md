# Data Packet Spec

A data packet is the typed output of a stage. It flows from one stage to the next
via the `stage_packets` table. Stages do not pass data in memory — they write to
the blackboard and the next stage reads from it. In this stencil, `stage_runtime.py`
performs the packet write after a stage returns, so read/plan stages do not mutate
domain tables.

Workflows add a second trace layer: `workflow_runs` records the whole
multi-discipline job, and `workflow_steps` records each stage result. The stage
packet remains the actual handoff data.

## Envelope (all packets)

Every packet includes this envelope regardless of stage:

```json
{
  "stage": "01_read | 02_plan | 03_execute",
  "discipline": "<discipline-folder-name>",
  "entity_id": "<uuid>",
  "workspace_id": "<uuid>",
  "created_at": "<iso8601>"
}
```

## Stage 01 — Read packet

```json
{
  "stage": "01_read",
  "discipline": "...",
  "entity_id": "...",
  "workspace_id": "...",
  "state": {
    "entity": {},           // the entity row
    "prior_decisions": [],  // recent decisions for this entity
    "learnings": [],        // active learnings for this entity
    "<domain_field>": {}    // add domain-specific reads here
  },
  "data_gaps": [],          // missing optional data (does not block planning)
  "ready_for_plan": true
}
```

## Stage 02 — Plan packet

```json
{
  "stage": "02_plan",
  "discipline": "...",
  "entity_id": "...",
  "workspace_id": "...",
  "plan": {
    "summary": "<one sentence>",
    "actions": [
      {
        "id": "<action_id>",
        "type": "<action_type>",
        "description": "<what this does in plain language>",
        "reversible": true,
        "requires_gate": false,
        "payload": {}
      }
    ]
  },
  "ready_for_execute": true
}
```

## Stage 03 — Result packet

```json
{
  "stage": "03_execute",
  "discipline": "...",
  "entity_id": "...",
  "workspace_id": "...",
  "results": [
    {
      "action_id": "<id>",
      "status": "done | failed | skipped",
      "outcome": {},
      "error": null
    }
  ],
  "summary": "<plain language: what happened>",
  "all_passed": true
}
```

## Rules

1. Packets are immutable once written. A re-run writes a new packet, not an update.
2. The `stage` field is the primary key for lookup within a workspace.
3. `data_gaps` in the read packet are informational — they describe what is missing
   but do not block the plan stage. The plan stage decides whether a gap is blocking.
4. `requires_gate: true` on any action means the execute stage MUST check gate
   resolution before running that action.
5. `ready_for_plan` and `ready_for_execute` are the handoff signals. If false,
   the next stage should not proceed and should surface the reason to the operator.
