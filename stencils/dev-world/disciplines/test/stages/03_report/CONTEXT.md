# test / 03_report

**Job:** Write the triage report. Tell the next developer exactly what is red,
why, and what to do about it.

## Inputs
- Classified failure list from 02_triage

## Process
1. Write the headline summary first — the numbers that matter at a glance
2. List new failures with enough detail to act on immediately
3. List known failures briefly — named but not detailed
4. Note flaky tests and collection errors separately
5. End with the action list: who fixes what, using which discipline

## Report format

```
TEST REPORT — <date>

HEADLINE
  N passed · N failed (N new · N known) · N errored

NEW FAILURES (fix these before committing)
  tests/test_foo.py::test_bar_returns_none
    Likely cause: change in foo.py:47 removed the None guard
    Owner: debug discipline → 01_reproduce

  tests/test_auth.py::test_login_invalid_token
    Likely cause: JWT signature key rotated in config but test still uses old key
    Owner: debug discipline → 02_isolate (environment issue, not logic)

KNOWN FAILURES (pre-existing, tolerated)
  tests/test_legacy.py::test_old_import — in baseline since 2024-03-01

FLAKY (intermittent, investigate separately)
  tests/test_sync.py::test_concurrent_writes — fails ~1 in 5 runs, timing issue

COLLECTION ERRORS (fix first — these hide other failures)
  tests/test_broken.py — ImportError: cannot import 'old_module'

ACTION LIST
  1. Fix new failures via debug discipline before next commit
  2. Fix collection error in test_broken.py (broken import)
  3. File issue for flaky test_concurrent_writes — do not block on it
```

## Gate
None. Report only.

## Done when
Report written with headline, classified failures, and action list.
The report is the deliverable — not a fixed suite. Fixing comes from `debug`.
