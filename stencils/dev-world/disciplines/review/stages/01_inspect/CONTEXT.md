# review / 01_inspect

**Job:** Read the diff and every touched file. Trace the real runtime path.
No assessment yet — just read.

## Inputs
- The diff or change to review (file list, PR, or explicit diff)

## Process
1. Read the diff in full — every line changed
2. Open every touched file completely, not just the changed lines. Diffs lie
   by omission: the unchanged lines around a change are often where the bug hides
3. Trace the runtime path end-to-end: if a function changed, trace every caller;
   if a DB column changed, trace every reader and writer; if a route changed,
   trace the request from entry to response
4. Note any files the diff did NOT touch that you would have expected it to
   (missing test file, missing migration, missing config update)
5. Do not form judgments yet — just build a complete picture

## Outputs
- List of every file touched and what changed in it
- Real runtime path traced (not assumed from the diff)
- List of files conspicuously absent from the diff

## Gate
None. Read-only.

## Done when
You have read every touched file, traced the runtime path, and noted absences.
If the diff references symbols you cannot find, grep for them before proceeding.
Never assess what you have not fully read.
