# feature — Stage Router

**Job:** Add something new to the codebase safely — with a plan, a real build,
tests, and a verified gate before declaring it done.

## Stage map

| the task is…                              | entry stage | runs through      |
|-------------------------------------------|-------------|-------------------|
| full feature from scratch                 | `01_plan`   | 01 → 02 → 03 → 04 |
| plan done, need build only                | `02_build`  | 02 → 03 → 04      |
| build done, need test + verify            | `03_test`   | 03 → 04           |

## Stages

```
stages/
  01_plan/    scope the feature, map blast radius, define the interface
  02_build/   implement — smallest change that adds the capability
  03_test/    write tests that cover the new path; run the suite
  04_verify/  commit_gate passes; self-review with post_change_review.md
```

## Law

- `01_plan` includes a `who_calls.py` run on any symbol the feature touches.
- `02_build` matches the surrounding code's style, naming, and comment density.
- `03_test` adds at least one test covering the happy path and one edge case.
- Nothing is done until `commit_gate.py` passes in `04_verify`.
