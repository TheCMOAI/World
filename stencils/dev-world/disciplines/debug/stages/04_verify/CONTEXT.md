# debug / 04_verify

**Job:** Prove the fix is clean across the whole suite. Gate before committing.

## Inputs
- Fix and new test from 03_fix

## Process
1. Run `python lib/commit_gate.py`
2. If gate blocks: read which tests are newly red, fix them, re-run
3. If gate passes: the fix is clean

## Outputs
- `commit_gate.py` exit 0
- A summary: what was broken, what was fixed, what test now covers it

## Gate
`commit_gate.py` must return exit 0. This is non-bypassable.

## Done when
Gate passes. The summary is written. Ready to commit.

Never report this stage done if the gate is still blocking.
The gate is the definition of done for a bug fix.
