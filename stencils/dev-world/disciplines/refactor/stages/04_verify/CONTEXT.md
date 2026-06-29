# refactor / 04_verify

**Job:** Gate. Suite no redder than before. Diff shows structure changed, behavior did not.

## Inputs
- Refactored code from 03_refactor

## Process
1. Run `python lib/commit_gate.py`
2. If gate blocks: read the new failures — are they behavior changes or test
   brittleness? Fix behavior changes; update brittle tests that test internals
   (but only if the test was testing the wrong thing — not to make failures go away)
3. Review the diff: every line changed should be structural, not behavioral.
   If you see logic changes, stop and investigate

## Outputs
- `commit_gate.py` exit 0
- Diff reviewed: only structural changes present
- Commit summary written

## Gate
`commit_gate.py` must return exit 0. Non-bypassable.

## Commit summary format
```
refactor <target name>

<one sentence: what structural change was made>
<one sentence: what behavior was preserved>
<one sentence: what coverage was added in 02_cover>
```

## Done when
Gate passes. Diff confirms structure-only change. Summary written.
