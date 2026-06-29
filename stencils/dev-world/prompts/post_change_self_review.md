# Post-Change Self-Review Prompt

Use this after any non-trivial code change. Paste it back into the active
Claude Code or Codex session, or let `lib/review_diff.py` inject it automatically
during the Ringer. Run it before declaring any discipline stage "done."

---

```text
You just wrote code in this repo. Stop building and review your own change as if
you did not trust the author.

Intent:
<one sentence describing what the change was supposed to do>

Changed files:
<paste git diff --name-only output, or say "read git diff from the repo">

Review rules:

1. Re-open every touched file and the direct caller/callee files. Do not review
   from memory or from the diff alone. Diffs lie by omission — the unchanged
   lines around a change are often where the bug hides.

2. Reconstruct the runtime path affected by the change end-to-end. Trace from
   the entry point to the final output. If the path does not match what the intent
   described, that is a finding.

3. Check source-of-truth alignment. If this change moves logic, does the old
   location now have a stale copy? If this adds a new table, is it in schema-map.md?
   If this adds a new discipline stage, is it in the CONTEXT.md router? Stale
   documentation is a bug.

4. Check blast radius. Run `python lib/who_calls.py <changed_symbol>` on every
   renamed or behavior-changed function. Verify callers still get what they expect.
   A caller that breaks silently is worse than a caller that throws.

5. Check tests and gates. Is there a test that would have caught this bug if it had
   been there before? If not, why not, and is that acceptable? If this change adds
   a new public behavior, is there a test for it? If this change touches a gated
   action, is the gate still in place?

6. Check what was NOT touched that should have been. Missing migration for a schema
   change. Missing CONTEXT.md update for a new stage. Missing requirements.txt entry
   for a new dependency. Absences are findings.

7. Run `python lib/commit_gate.py`. If it blocks, the stage is not done regardless
   of what the diff looks like.

Output exactly:

Verdict: PASS | FIX-FIRST | BLOCKED

Runtime path touched:
- <the actual path traced, not an architecture guess>

Findings:
- [BLOCKER|HIGH|MEDIUM|LOW] <file:line> — <what is wrong> — <how to fix>

Tests/gates run:
- <commands and results, or explicit "not run yet">

Required follow-up:
- <specific edits still needed, or "none">

If you find a HIGH or BLOCKER finding, fix it before claiming the task is done.
Do not explain it away as acceptable unless you can point to a contract that proves it is.
```

---

## When to use this

- After every `03_fix` stage in `debug/`
- After every `02_build` stage in `feature/`
- After every `03_refactor` stage in `refactor/`
- Automatically injected by `lib/ringer.py` during the adversarial review stage

## How review_diff.py uses this

`lib/review_diff.py` injects this prompt into a fresh LLM session with the diff
pre-loaded. Each pass is an independent adversarial review — the reviewers do not
share context and cannot talk each other into accepting a bad change. The Ringer
runs three passes by default and blocks on any HIGH or BLOCKER finding.
