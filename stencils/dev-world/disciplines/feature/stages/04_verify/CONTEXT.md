# feature / 04_verify

**Job:** Gate. No new failures across the whole suite. Feature is ready to commit.

## Inputs
- Build from 02_build, tests from 03_test

## Process
1. Run `python lib/commit_gate.py`
2. If gate blocks: read which tests are newly red, fix them, re-run
3. If gate passes: write the commit summary and declare done

## Outputs
- `commit_gate.py` exit 0
- Commit summary: what was added, what tests cover it, what was explicitly NOT changed

## Gate
`commit_gate.py` must return exit 0. Non-bypassable.

## Commit summary format
```
add <feature name>

<one sentence: what it does>
<one sentence: what tests cover it>
<one sentence: what it does NOT do — scope boundary>
```

## Done when
Gate passes and summary is written. Not before.
The gate is the definition of done for a feature.
