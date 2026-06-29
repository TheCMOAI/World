# feature / 02_build

**Job:** Implement the plan. Smallest change that adds the capability.

## Inputs
- Plan from 01_plan: scope, interface, blast radius, boundary

## Process
1. Write the implementation — match the surrounding code's style, naming,
   and comment density exactly. Do not introduce new patterns or abstractions
   the codebase does not already use
2. Check every caller in the blast radius — does the change break any of them?
3. If the feature adds a new public function or route, ensure existing callers
   are unaffected (or updated intentionally)
4. Do not also fix bugs you find along the way — note them, fix them separately

## Outputs
- The feature implemented in the identified file(s)
- All blast-radius callers checked and unbroken
- Nothing outside the scope boundary touched

## Gate
None here — `03_test` and `04_verify` are the gates.

## Done when
The feature exists and does what was scoped. Callers are unbroken.
Do not declare done — move to `03_test` immediately.
