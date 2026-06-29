# feature / 01_plan

**Job:** Scope the feature, map the blast radius, define the interface. No code changes.

## Inputs
- Operator description of what to build
- Any constraints (must not break X, must match Y interface)

## Process
1. Understand what the feature does in one sentence — if you cannot write it in
   one sentence, the scope is too wide; ask the operator to narrow it
2. Find where it lives: what file(s) will it add to or change?
3. Run `python lib/who_calls.py <symbol>` on anything the feature touches that
   other code already depends on
4. Define the interface: what goes in, what comes out, what the caller sees
5. List what the feature must NOT do — scope boundaries prevent drift during build

## Outputs
- Feature scoped in one sentence
- File(s) to add or change, identified
- Blast radius: what existing code this touches
- Interface defined: inputs, outputs, behavior
- Scope boundary: what is explicitly out of scope

## Gate
None. Read-only.

## Done when
You can describe the feature, where it lives, what it touches, and what its
interface is — without having written a single line of code yet. If any of those
are unclear, clarify before moving to `02_build`.
