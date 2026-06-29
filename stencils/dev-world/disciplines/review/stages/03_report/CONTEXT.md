# review / 03_report

**Job:** Write the findings report. Every finding gets a severity, a location,
and a clear explanation of what is wrong and why it matters.

## Inputs
- Raw findings from 02_assess

## Process
1. Assign severity to each finding (see scale below)
2. Write each finding as a structured entry
3. Write the overall verdict at the top

## Severity scale

| level    | definition                                                              |
|----------|-------------------------------------------------------------------------|
| blocker  | will break in production, silently corrupts data, or causes data loss   |
| high     | likely to cause a bug or regression under normal use                    |
| medium   | missing test, code smell, incorrect assumption — real consequence        |
| low      | naming, style preference, minor improvement — does not block shipping   |

## Finding format

```
[HIGH] auth/middleware.py:47 — missing null check on user_id

The `require_auth` decorator passes `user_id` directly to `get_user()` without
checking for None. If the JWT is valid but contains no sub claim, `user_id` is
None and `get_user(None)` returns the first row in the users table.

Fix: add `if not user_id: raise AuthError("missing subject")` before line 47.
```

Each finding must have:
- Severity in brackets
- File and line number
- One-line description
- Why it matters (what breaks, when, under what condition)
- What to do (specific, actionable)

## Verdict

At the top of the report, write the verdict before the findings:

```
VERDICT: SHIP | FIX | BLOCKED

N blocker(s) · N high(s) · N medium(s) · N low(s)
```

| condition                          | verdict  |
|------------------------------------|----------|
| zero blockers, zero highs          | SHIP     |
| zero blockers, one or more highs   | FIX      |
| one or more blockers               | BLOCKED  |

## Done when
Report is written with verdict at top, all findings structured with severity,
location, explanation, and fix. A report with zero findings must still say why —
"no findings" is a conclusion, not a skip.
