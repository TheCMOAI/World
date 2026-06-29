# <Discipline> / 01_identify

**Job:** Understand the target. No code changes.

## Inputs
- Operator description of the task
- File path, function name, or symptom to start from

## Process
1. Read the relevant file(s)
2. Grep for the symbol if the location is unclear
3. Understand what the target does and who depends on it
4. Run `python lib/who_calls.py <symbol>` if the target is a shared function or table

## Outputs
- Location confirmed: file + line
- Purpose understood: what this code does
- Blast radius noted: who else touches this

## Gate
None. Read-only.
