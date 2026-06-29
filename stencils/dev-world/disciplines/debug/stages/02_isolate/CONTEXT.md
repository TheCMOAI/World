# debug / 02_isolate

**Job:** Find the exact line, function, or condition causing the bug. No code changes.

## Inputs
- Reproduction from 01_reproduce
- The file or approximate area identified in 01

## Process
1. Read the file — understand what it is supposed to do
2. Run `python lib/who_calls.py <function>` on any function you think is the cause
3. Trace the data path: what goes in, where does it diverge from what should happen
4. Narrow to the exact line or condition — not "somewhere in this file" but "line 47, this branch"
5. Check if other callers are affected by the same root cause

## Outputs
- Exact root cause: file, line, what the code does vs. what it should do
- Blast radius: list of callers that may be affected (from who_calls.py)
- Whether the fix is local (one file) or systemic (multiple callers)

## Gate
None. This stage is read-only.

## Done when
You can point to the exact line and explain in one sentence why it is wrong.
"The bug is in `foo.py:47` — the condition checks `x > 0` but should check `x >= 0`."
