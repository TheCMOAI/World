# refactor / 03_refactor

**Job:** Restructure. Behavior unchanged, callers unaffected, tests still pass.

## Inputs
- Map from 01_map, coverage from 02_cover

## Process
1. Make the structural change — rename, reorganize, extract, inline, simplify
2. After each meaningful sub-change, run the targeted tests:
   `python lib/run_tests.py --select <test_file>`
   Do not batch up large changes without checking — each sub-step should stay green
3. Check every caller in the blast radius — nothing broken
4. Do not fix bugs discovered during the refactor — note them in a comment or
   a separate file and fix them in a dedicated `debug` discipline run after this

## The hard rule
If you find yourself changing what the code does — not just how it's structured —
stop. That is not a refactor. Either the scope is wrong or you found a bug.
Surface it and get operator input before continuing.

## Outputs
- Restructured code with identical external behavior
- All pre-existing tests still passing
- No new behavior introduced

## Gate
None here — `04_verify` is the gate.

## Done when
The structure is improved and the targeted tests still pass.
Move to `04_verify` — do not declare done until the gate runs.
