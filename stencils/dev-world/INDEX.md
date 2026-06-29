# Dev World — Domain Index

> The single-read map of the development domain. Every discipline, its job,
> and its stage chain. Read this when you need the whole picture at once.

## The engine (`lib/` — these actually run)

| script           | what it does                                                                 |
|------------------|------------------------------------------------------------------------------|
| `run_tests.py`   | runs the test suite, survives broken collectors, reports pass/fail/error     |
| `who_calls.py`   | live grep blast-radius — who references a symbol across the codebase         |
| `commit_gate.py` | runs the suite, **blocks any change that newly breaks a test** vs baseline   |

## Disciplines

| discipline  | what it handles                              | stage chain                                  |
|-------------|----------------------------------------------|----------------------------------------------|
| `debug`     | something is broken — find it, fix it, prove it | 01_reproduce → 02_isolate → 03_fix → 04_verify |
| `feature`   | add something new, safely                    | 01_plan → 02_build → 03_test → 04_verify     |
| `refactor`  | restructure with behavior unchanged          | 01_map → 02_cover → 03_refactor → 04_verify  |
| `review`    | adversarial read of a diff before it ships   | 01_inspect → 02_assess → 03_report           |
| `test`      | run / triage / report on the suite           | 01_run → 02_triage → 03_report               |

## Workflows

| workflow | what it is                                                                   | stage chain                                     |
|----------|------------------------------------------------------------------------------|-------------------------------------------------|
| `ringer` | the gauntlet every finished change must pass — tests + review + verdict      | 01_test → 02_review → 03_verdict                |

## The 5-phase loop (every discipline is a specialization of this)

```
IDENTIFY → PLAN → BUILD → TEST → VERIFY
```

| discipline  | IDENTIFY      | PLAN          | BUILD         | TEST          | VERIFY        |
|-------------|---------------|---------------|---------------|---------------|---------------|
| `debug`     | 01_reproduce  | 02_isolate    | 03_fix        | 04_verify     | 04_verify     |
| `feature`   | 01_plan       | 01_plan       | 02_build      | 03_test       | 04_verify     |
| `refactor`  | 01_map        | 02_cover      | 03_refactor   | 04_verify     | 04_verify     |
| `review`    | 01_inspect    | 02_assess     | —             | —             | 03_report     |
| `test`      | 01_run        | —             | —             | 01_run        | 02_triage     |

## Law

1. Every non-trivial change: IDENTIFY → PLAN → BUILD → TEST → VERIFY.
2. Nothing is "done" until `commit_gate.py` passes.
3. Blast radius before load-bearing edits (`who_calls.py`).
4. A bug gets a test. The same bug never ships twice.
