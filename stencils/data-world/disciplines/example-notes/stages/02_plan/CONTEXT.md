# example-notes / 02_plan

**Job:** Decide what note action to take based on the operator request and current state.

## Inputs
- State packet from `01_read`
- Operator intent (create_note, summarize, retrieve)

## Process
1. Read the state packet
2. Determine the action type from operator intent
3. For create_note: validate content against note-conventions.md
4. For summarize: group existing notes by topic
5. Produce a typed plan - no mutations yet

## Outputs
```json
{
  "stage": "02_plan",
  "discipline": "example-notes",
  "entity_id": "...",
  "workspace_id": "...",
  "plan": {
    "summary": "Create 1 new note for entity",
    "actions": [
      {
        "id": "note_001",
        "type": "create_note",
        "description": "Add note: 'Prefers email contact over phone'",
        "reversible": true,
        "requires_gate": false,
        "payload": {
          "content": "Prefers email contact over phone",
          "topic": "communication_preference"
        }
      }
    ]
  },
  "ready_for_execute": true
}
```

## Gate
None for note creation. Gate if deleting or archiving all notes (irreversible at scale).
