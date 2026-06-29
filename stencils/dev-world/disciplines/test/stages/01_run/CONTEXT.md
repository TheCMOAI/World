# test / 01_run

**Job:** Run the suite. Capture the raw result. Never interpret yet.

## Inputs
- Scope: full suite, a specific file, or a keyword filter

## Process
1. Always use `python lib/run_tests.py`, never bare `pytest` from the repo root.
   The catch-net exists because bare pytest can abort collection silently on
   broken or vendored test files and report a hollow green.
2. For a full run: `python lib/run_tests.py`
3. For a scoped run: `python lib/run_tests.py --select <path or keyword>`
4. Capture: passed count, failed count, errored count, and the list of failing
   test IDs exactly as pytest reports them

## Outputs
- Raw counts: N passed · N failed · N errored
- Failing test IDs (full pytest node IDs, e.g. `tests/test_foo.py::test_bar`)
- Whether any tests errored during collection (different from test failures —
  a collection error means a file could not be imported)

## Gate
None. Run-only.

## Done when
The run completed and you have the raw counts and failure list.
If collection errors occurred, note them separately — they mask real test results
and must be investigated before the triage is meaningful.
