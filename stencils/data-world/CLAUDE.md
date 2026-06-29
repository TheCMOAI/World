# World — Claude Code Entry Point

> You are operating inside a **data-world** — a structured operating domain
> with disciplines, a Postgres blackboard, and a set of entities you act on
> behalf of. This file is the Claude Code entry point. Read it, then read
> `agent.md` for the domain-specific operator identity and context.

## Layer 0 — Where you are

This folder IS the World. The disciplines underneath you each own one job.
The blackboard (Postgres) is the only source of truth. You read from it before
acting and write outcomes back after.

## Navigation

```
agent.md          ← your domain identity and operator voice (read this next)
disciplines/      ← one folder per job — read the CONTEXT.md inside each
brain/            ← schema-map.md (what's in the DB) + access-contract.md
lib/              ← stage_runtime.py dispatches your tool calls; tools.py = your toolbelt
                     watch.py + dispatch.py = the scheduler (disciplines wake themselves)
                     workflow_runtime.py = multi-discipline workflow runner
migrations/       ← run 001_init.sql to initialize the blackboard, then 002_activation.sql
                     for the scheduler (see brain/activation-model.md)
workspaces/       ← per-entity session mirrors (DB is authoritative, not these files)
```

## Your tools (the only actions you take)

```
run_stage <discipline> <stage> <args>   activate a stage in a discipline
run_workflow <workflow> <entity_id>      run a multi-discipline workflow
read      <table> [filter]              read from the blackboard
manage    <entity.action> <payload>     create / update / archive an entity
gate      <question> <workspace_id>     surface a decision before a mutation
```

No raw SQL. No shell commands outside lib/ scripts. No file writes outside workspaces/.
The tools are the fence.

## The three rules before you touch anything

1. **Read the blackboard first.** Never assert what the current state is — read it.
2. **Run the right stage.** Check the discipline's CONTEXT.md to find the right entry stage.
3. **Gate before you mutate.** Any irreversible or externally visible action needs a gate.

## Setup checklist (first run)

- [ ] `DATABASE_URL` set in environment
- [ ] `psql $DATABASE_URL < migrations/001_init.sql` run
- [ ] `python lib/world_doctor.py` passes
- [ ] At least one entity created via `manage entity.create`
- [ ] `python lib/workflow_runtime.py --workflow service-business-ops --entity-id <uuid> --json` passes

## Troubleshooting

**"No module named psycopg2"** — run `pip install psycopg2-binary`
**"DATABASE_URL not set"** — `export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname`
**Stage returns error: "Entity not found"** — create the entity first with `manage entity.create`
