# debug — Stage Router

**Job:** Something is broken. Reproduce it, isolate the cause, fix the smallest
thing that makes it stop, and prove it's gone.

## Stage map

| the task is…                              | entry stage    | runs through        |
|-------------------------------------------|----------------|---------------------|
| full debug from scratch                   | `01_reproduce` | 01 → 02 → 03 → 04   |
| cause already known, need fix + proof     | `03_fix`       | 03 → 04             |
| fix written, need proof only              | `04_verify`    | 04 only             |

## Stages

```
stages/
  01_reproduce/   confirm the bug exists and can be triggered reliably
  02_isolate/     find the exact line, function, or condition causing it
  03_fix/         write the smallest change that stops the bug
  04_verify/      prove it with a test + commit_gate
```

## Law

- Do not touch code in `01_reproduce` or `02_isolate`. Reading only.
- The fix in `03_fix` ships with a test that failed before and passes after.
- `04_verify` is not done until `commit_gate.py` passes.
- Never report the bug fixed if `04_verify` still shows it failing.
