# ringer — The Gauntlet

**Job:** Put a finished change through the full quality gauntlet before it ships.
Tests + adversarial review + verdict. Nothing is "done" until the ringer passes.

Run this after a `debug`, `feature`, or `refactor` discipline finishes —
before the final commit or PR.

## Stage map

| stage       | what it does                                              |
|-------------|-----------------------------------------------------------|
| `01_test`   | full suite via `commit_gate.py` — zero new failures       |
| `02_review` | adversarial read of the diff — find what the author missed |
| `03_verdict`| final verdict — ship / fix and re-run / escalate          |

## How to run

```bash
# Run stages in sequence. Each must pass before the next starts.
python lib/run_tests.py               # 01_test
# then review the diff via disciplines/review/ → 01_inspect → 02_assess → 03_report
python lib/commit_gate.py             # final gate
```

## Verdict rules

| condition                        | verdict  | action                                 |
|----------------------------------|----------|----------------------------------------|
| gate passes + no blockers/highs  | SHIP     | safe to commit and push                |
| gate passes + highs found        | FIX      | fix highs, re-run ringer from 01_test  |
| gate blocks                      | BLOCKED  | fix new failures, re-run from 01_test  |
| blocker found in review          | BLOCKED  | fix blocker, re-run ringer             |

## Law

- The ringer cannot be skipped for any meaningful code change.
- "Looks fine" is not a passing review. The review must find and document findings.
- A SHIP verdict with open medium/low findings is acceptable — note them in the
  commit message or a follow-up ticket, do not re-run the full gauntlet for them.
- Never report SHIP if `commit_gate.py` has not been run in this ringer session.
