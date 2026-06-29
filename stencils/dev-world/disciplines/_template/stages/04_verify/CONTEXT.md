# <Discipline> / 04_verify

**Job:** Gate. No new failures across the whole suite.

## Inputs
- Change from 03_build

## Process
1. Run `python lib/commit_gate.py`
2. If blocked: read new failures, fix them, re-run
3. If passed: done

## Outputs
- `commit_gate.py` exit 0
- Summary: what changed and what now covers it

## Gate
`commit_gate.py` exit 0. Non-bypassable.

## Done when
Gate passes. Not before.
