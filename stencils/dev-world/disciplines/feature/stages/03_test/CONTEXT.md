# feature / 03_test

**Job:** Write tests that cover the new path. Run the suite. No new red.

## Inputs
- Implemented feature from 02_build

## Process
1. Write at least one test for the happy path — the feature working as intended
2. Write at least one test for the primary edge case — empty input, missing
   dependency, boundary condition, or the most likely misuse
3. Run `python lib/run_tests.py --select <new_test_file>` — new tests must pass
4. Run `python lib/run_tests.py` on the broader scope to confirm nothing regressed

## Outputs
- New test file (or additions to an existing test file) in `tests/`
- All new tests passing
- No regressions in the broader suite

## What counts as a test
- Happy path: feature does what it claims when given valid input
- Edge case: feature handles the most likely failure mode gracefully
- Not required here: exhaustive coverage, mocking everything, testing internals

## Gate
All new tests must pass before moving to `04_verify`.

## Done when
New tests pass. Suite is no redder than before. Move to `04_verify`.
