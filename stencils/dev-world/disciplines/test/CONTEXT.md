# test — Stage Router

**Job:** Run the suite, understand what's red and why, and produce a triage
report that tells the next developer exactly what to fix.

## Stage map

| the task is…                          | entry stage  | runs through  |
|---------------------------------------|--------------|---------------|
| full run + triage + report            | `01_run`     | 01 → 02 → 03  |
| run done, need triage only            | `02_triage`  | 02 → 03       |
| triaged, need written report only     | `03_report`  | 03 only       |

## Stages

```
stages/
  01_run/     run the suite with run_tests.py; capture pass/fail/error counts
  02_triage/  read the failures — pre-existing vs newly broken vs flaky
  03_report/  write the triage — what is red, why, and who owns each failure
```

## Law

- Always use `run_tests.py`, never bare `pytest`. The catch-net exists for a reason.
- `02_triage` distinguishes pre-existing red (in baseline) from new red (not in
  baseline). Do not treat all failures as equal.
- `03_report` names an owner for each new failure — the discipline that should fix
  it (`debug`, `feature`, `refactor`) and the entry stage.
- A "clean" report means zero new failures vs baseline — not zero failures total.
