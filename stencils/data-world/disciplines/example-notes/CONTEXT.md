# example-notes — Stage Router

**Job:** Create, summarize, and retrieve notes attached to an entity.
This is a fully worked example discipline — read it to understand the pattern,
then delete it and replace with your real disciplines.

## Stage map

| request kind             | entry stage    | runs through  |
|--------------------------|----------------|---------------|
| create a new note        | `01_read`      | 01 → 02 → 03  |
| summarize existing notes | `01_read`      | 01 → 02 → 03  |
| retrieve notes only      | `01_read`      | 01 only       |

## Stages

```
stages/
  01_read/     read existing notes for the entity from the blackboard
  02_plan/     decide what to create or summarize based on the operator request
  03_execute/  write the new note or summary back to the blackboard
```

## What this discipline owns

- Write surface: `entity_notes` table (see migrations/001_init.sql — add this table)
- Does NOT mutate: entities, workspaces, decisions, learnings

## Shared resources

- `references/note-conventions.md` — rules for note format and length
- `lib/exec.py` — text utilities (truncate, clean whitespace)
