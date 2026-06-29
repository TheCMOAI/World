# example-notes / 03_execute

**Job:** Act on the plan. Write the note to the blackboard. Log the activity.

## Inputs
- Plan packet from `02_plan`

## Process
1. Read plan packet from workspace
2. For each action: execute the handler, write to `entity_notes`, log to `entity_activity_log`
3. Return result packet

## Outputs
```json
{
  "stage": "03_execute",
  "discipline": "example-notes",
  "entity_id": "...",
  "workspace_id": "...",
  "results": [
    {
      "action_id": "note_001",
      "status": "done",
      "outcome": { "note_id": "...", "content": "..." },
      "error": null
    }
  ],
  "summary": "1 of 1 actions completed",
  "all_passed": true
}
```

## Gate
None for create_note. Gate required if bulk-deleting notes.

## Verify
After writing: re-read the row from `entity_notes` to confirm it landed.
Never report success on a write you have not verified.
