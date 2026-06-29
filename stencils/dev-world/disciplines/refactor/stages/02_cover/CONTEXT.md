# refactor / 02_cover

**Job:** Ensure test coverage exists for the behavior being restructured before
touching a line. Never refactor without a safety net.

## Inputs
- Map from 01_map: behavior description, caller list, coverage inventory

## Process
1. For each behavior in the coverage inventory that has NO test: write one
2. Tests must cover the observable contract — what callers depend on — not internals
3. Run `python lib/run_tests.py --select <test_file>` to confirm new tests pass
4. Do not cover implementation details that will change during the refactor —
   only cover the external behavior that must survive it

## Outputs
- New or extended tests covering all behaviors in the contract surface
- All new tests passing before the refactor begins

## What "coverage" means here
Not 100% line coverage. Coverage of the **contract** — every behavior a caller
depends on must have a test that will fail if that behavior breaks.

If a caller depends on `foo()` returning a list, there must be a test that asserts
`foo()` returns a list. That test will catch a refactor that accidentally returns None.

## Gate
All new coverage tests must pass before moving to `03_refactor`.
If you cannot write a test for a behavior, note why and surface it to the operator —
do not proceed to refactor uncovered behavior.

## Done when
Every contract-surface behavior has a test. All tests pass.
