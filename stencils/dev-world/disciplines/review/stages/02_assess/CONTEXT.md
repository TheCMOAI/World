# review / 02_assess

**Job:** Find what the author missed. Be adversarial. Assume something is wrong
and look for it — do not look for reasons the change is fine.

## Inputs
- Complete picture from 01_inspect: touched files, runtime path, absences

## Process

### Correctness pass
- Does the change do what it claims? Trace the logic against the stated intent
- Are there off-by-one errors, wrong comparisons, missing null checks, or
  incorrect assumptions about types or state?
- Does the change handle the unhappy path (empty input, missing dependency,
  concurrent access, network failure)?

### Caller pass
- Does every caller of a changed function still get what it expects?
- If a return type or argument changed, are all callers updated?
- Are there callers in OTHER files not caught in the diff?

### Test pass
- Is there a test that would have caught the bug this change claims to fix?
- Do the new tests actually test the behavior, or do they test the implementation?
- Could these tests pass even if the feature is broken?

### Absence pass
- Is there a migration missing for a schema change?
- Is there a config update missing?
- Is there a dependent system that should have changed but did not?

## Outputs
- Raw findings list: every issue found, with file and line, before severity is assigned

## Gate
None. Assessment only.

## Done when
You have run all four passes. Move to `03_report` to assign severity and write findings.
