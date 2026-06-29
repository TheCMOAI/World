# refactor — Stage Router

**Job:** Restructure code without changing observable behavior. Every external
caller keeps working. Every test that passed before still passes after.

## Stage map

| the task is…                              | entry stage  | runs through      |
|-------------------------------------------|--------------|-------------------|
| full refactor from scratch                | `01_map`     | 01 → 02 → 03 → 04 |
| map done, need coverage before refactor   | `02_cover`   | 02 → 03 → 04      |
| covered, ready to restructure             | `03_refactor`| 03 → 04           |

## Stages

```
stages/
  01_map/       read the target — what it does, who calls it, what it touches
  02_cover/     ensure test coverage exists for the behavior being restructured
  03_refactor/  restructure — behavior unchanged, callers unaffected
  04_verify/    commit_gate passes; diff shows no behavior change
```

## Law

- Never start `03_refactor` without coverage in `02_cover`. Refactoring without
  tests is rewriting with no safety net.
- `03_refactor` changes structure only — no new behavior, no bug fixes bundled in.
  If you find a bug while refactoring, fix it in a separate commit.
- The diff in `04_verify` should show zero changes to test assertions.
- `commit_gate.py` must pass before calling this done.
