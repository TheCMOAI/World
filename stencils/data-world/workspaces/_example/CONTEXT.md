# Workspace: _example

This folder mirrors the DB state for a workspace session. It is generated, not
authoritative — the database is the source of truth. Files here are human-readable
snapshots you can inspect or diff.

## Structure

When a workspace is active, the harness may write:

```
workspaces/<entity-slug>/
  state.json         ← latest 01_read output for this entity
  plan.json          ← latest 02_plan output
  result.json        ← latest 03_execute output
  decisions.json     ← decisions logged for this entity
  gates.json         ← open/resolved gates
```

## Rule

Never edit files here. They will be overwritten by the next stage run.
To see current state, read from the database. These files exist for legibility only.
