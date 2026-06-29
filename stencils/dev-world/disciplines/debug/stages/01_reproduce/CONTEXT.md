# debug / 01_reproduce

**Job:** Confirm the bug exists and can be triggered reliably. No code changes.

## Inputs
- Bug description or error message from the operator
- File path, test name, or symptom to start from

## Process
1. Read the error message or symptom carefully
2. Find the relevant file(s) — grep, read, trace the call stack
3. Run `python lib/run_tests.py --select <path>` to see if there's a failing test
4. If no test: reproduce manually — describe exactly what input triggers the bug
5. Confirm the symptom is consistent (not flaky)

## Outputs
- Confirmed reproduction: what input triggers it, what output is wrong
- The failing test ID if one exists, or the manual repro steps if not
- The file and approximate line where the wrong behavior originates

## Gate
None. This stage is read-only.

## Done when
The bug can be triggered on demand and you know which file to look at next.
If you cannot reproduce it, stop and ask the operator for more detail — do not proceed to isolate a phantom.
