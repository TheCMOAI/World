# refactor / 01_map

**Job:** Read the target fully. Map what it does and who depends on it. No code changes.

## Inputs
- Operator description of what to restructure
- The target: file, function, module, or pattern to refactor

## Process
1. Read the target file(s) fully — understand what the code does, not just what
   it looks like
2. Run `python lib/who_calls.py <symbol>` on every public function or name
   the target exposes — this is the full blast radius
3. Note every caller and what it expects: return type, argument order, side effects
4. Identify what is safe to change (internals, naming, structure) vs. what is
   a contract (the interface callers depend on)
5. Check test coverage: which of the target's behaviors are currently tested?

## Outputs
- What the target does (behavior, not structure)
- Full blast radius: every external caller and what it expects
- Contract surface: the interface that must not change
- Coverage inventory: which behaviors have tests, which do not

## Gate
None. Read-only.

## Done when
You can describe the target's behavior, every caller's dependency on it, and the
line between safe-to-change and must-not-change — without having touched a file.
If the blast radius is larger than expected, surface it to the operator before continuing.
