# review — Stage Router

**Job:** Adversarially read a diff or change before it ships. Find what the
author missed — correctness bugs, broken callers, missing tests, regressions.

## Stage map

| the task is…                     | entry stage   | runs through  |
|----------------------------------|---------------|---------------|
| full review from a diff          | `01_inspect`  | 01 → 02 → 03  |
| inspection done, need assessment | `02_assess`   | 02 → 03       |
| assessment done, write report    | `03_report`   | 03 only       |

## Stages

```
stages/
  01_inspect/   read the diff; open every touched file; trace the real runtime path
  02_assess/    find bugs, broken callers, missing tests, style issues
  03_report/    write findings — blocker / high / medium / low — with file + line
```

## Law

- `01_inspect` re-opens the actual touched files — not just the diff. Diffs
  lie by omission. The real runtime path is what matters.
- `02_assess` is adversarial. Assume the author missed something. Look for it.
- `03_report` findings must include: severity, file, line, what is wrong, why
  it matters. "Looks fine" is not a finding.
- A clean report is one with zero blockers and zero highs — not one with no findings.

## Severity levels

| level    | means                                                        |
|----------|--------------------------------------------------------------|
| blocker  | will break in production or silently corrupts data           |
| high     | likely to cause a bug or regression under normal use         |
| medium   | code smell, missing test, style issue with real consequence  |
| low      | preference, naming, minor — note it, do not block on it      |
