# example-notes / 01_read

**Job:** Read existing notes for this entity from the blackboard.

## Inputs
- `entity_id` - which entity to read notes for
- `workspace_id` - the active workspace session

## Process
1. Read entity base state from `entities` table
2. Read existing notes from `entity_notes` table (limit 10, newest first)
3. Read any prior learnings relevant to this entity
4. Assemble state packet

## Outputs
```json
{
  "stage": "01_read",
  "discipline": "example-notes",
  "entity_id": "...",
  "workspace_id": "...",
  "state": {
    "entity": { "id": "...", "name": "..." },
    "existing_notes": [
      { "id": "...", "content": "...", "created_at": "..." }
    ],
    "learnings": []
  },
  "data_gaps": [],
  "ready_for_plan": true
}
```

## Gate
None. Read-only.
