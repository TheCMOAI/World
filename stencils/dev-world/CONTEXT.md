# Dev World — Layer 1 (Router)

> Answers: **"Where do I go?"** Given a development task, this file routes it
> to a discipline or workflow. Find the route, follow it, then read that
> folder's `CONTEXT.md` to pick the entry stage.

## Routing table

| the task is…                                              | route               | enters at      |
|-----------------------------------------------------------|---------------------|----------------|
| something is broken / returns wrong data / throws         | `disciplines/debug` | `01_reproduce` |
| add or build something new                                | `disciplines/feature` | `01_plan`    |
| restructure without changing behavior                     | `disciplines/refactor` | `01_map`    |
| review a diff or change before it ships                   | `disciplines/review` | `01_inspect`  |
| run the tests / what's red / triage the suite             | `disciplines/test`  | `01_run`       |
| put a finished change through the full gauntlet           | `workflows/ringer`  | `01_backend`   |

## How to route

```
task arrives
  → spans multiple capabilities? → workflows/ringer
  → single capability?           → disciplines/<name>/
  → then read CONTEXT.md in that folder to pick the entry stage
```

## Before you route — orient first

1. **Don't know where the target lives?** Read `INDEX.md`, then grep.
2. **Touching a named function or table?** Run `python lib/who_calls.py <name>`
   to see the blast radius before routing to a discipline.
3. **Is the suite already red where you're working?** Run
   `python lib/run_tests.py --select <path>` to get the baseline state so you
   can tell your breakage from pre-existing red.
4. **One-liner doc/comment fix?** Loop is light — fix and gate, skip the ceremony.

## Exit gate (every route)

No route is done until `python lib/commit_gate.py` passes. That is the single
non-bypassable exit condition. If it blocks, the route is not finished.
