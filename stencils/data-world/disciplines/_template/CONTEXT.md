# <Discipline Name> — Stage Router

> Layer 1 (local). Answers: given a request routed to this discipline, which
> stage handles it? Read this after the root operator has determined this
> discipline is the right one for the job.

## What this discipline does

One sentence. What job does this discipline own?

## Stage map

| request kind        | entry stage       | runs through     |
|---------------------|-------------------|------------------|
| <full run>          | `stages/01_read`  | 01 → 02 → 03     |
| <re-run from plan>  | `stages/02_plan`  | 02 → 03          |
| <verify only>       | `stages/03_execute` | 03 only        |

## Stages

```
stages/
  01_read/     gather current state from the blackboard and any external sources
  02_plan/     produce a typed plan packet — no mutations, no side effects
  03_execute/  act on the approved plan, write outcomes back to the blackboard
```

Add stages as needed. Numbering encodes execution order. Each stage folder has
its own `CONTEXT.md` (inputs / process / outputs / gate).

## What this discipline owns

- Write surface: `<table_name>` rows for the entity in scope
- Does NOT mutate: <list anything this discipline must not touch>

## Shared resources

- `references/` — frozen domain knowledge this discipline reads (conventions,
  rules, catalogs). Never improvised. Update deliberately.
- `lib/` — deterministic scripts (no AI). Shell these for mechanical work.
