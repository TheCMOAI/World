# debug / 03_fix

**Job:** Write the smallest change that stops the bug. Add a test that proves it.

## Inputs
- Root cause from 02_isolate
- Blast radius (list of callers to check after the fix)

## Process
1. Write the fix — smallest change that corrects the behavior
2. Check every caller in the blast radius — does the fix break any of them?
3. Write a test:
   - It must FAIL before the fix
   - It must PASS after the fix
   - It must live in `tests/` and be runnable via `run_tests.py`
4. Run `python lib/run_tests.py --select <test_file>` to confirm fix + test

## Outputs
- The fix (edited file(s))
- A new test that captures the bug
- Confirmation the targeted test passes

## Gate
None at this stage — `04_verify` is the gate.

## Done when
The specific test passes. Move to `04_verify` — do not declare done until
`commit_gate.py` confirms no new failures across the whole suite.
