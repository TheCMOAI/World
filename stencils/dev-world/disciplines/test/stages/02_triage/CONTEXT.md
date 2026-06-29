# test / 02_triage

**Job:** Classify each failure. Pre-existing vs. newly broken vs. flaky.
This is the decision layer — do not skip it and jump to "fix everything red."

## Inputs
- Raw failure list from 01_run
- Baseline from `lib/.test_baseline.json` (run `python lib/commit_gate.py --json`
  to get the known-failure set)

## Process

### Classify each failure as one of:

**New failure** — not in the baseline. Someone broke this. Needs a fix.
Priority: high. Owner: the discipline that caused the regression.

**Known failure** — in the baseline. Pre-existing red that was already accepted.
Priority: noted but not blocking. Do not fix during this run unless it is the
explicit task.

**Flaky** — fails intermittently, not consistently. Often timing, ordering,
or external dependency issues.
Priority: medium. Note it; do not block on it; investigate separately.

**Collection error** — the test file itself failed to import. Blocks all tests
in that file and hides real failures.
Priority: highest. Fix the import before anything else.

### For each new failure, identify:
- Which recent change likely caused it (check git log, check who_calls.py)
- Which discipline should own the fix: `debug` (if the feature code is wrong)
  or `test` itself (if the test is brittle and testing internals)

## Outputs
- Classified failure list: new / known / flaky / collection-error per test
- For new failures: likely cause and owner discipline
- Count of new failures (the number that matters for the gate)

## Gate
None. Classification only.

## Done when
Every failure in the raw list is classified. Move to `03_report`.
