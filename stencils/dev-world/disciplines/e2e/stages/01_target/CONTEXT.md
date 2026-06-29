# e2e / 01_target

**Job:** Identify the UI surface the change touches. Write a plain-language spec
of what to verify. No browser yet.

## Inputs
- Description of the change from the feature or debug discipline
- URL path or component name of the affected UI surface

## Process
1. Identify the page(s) or component(s) affected
2. Write the spec as a numbered list of user actions and expected outcomes:
   - "Navigate to /entities"
   - "Click 'Create Entity'"
   - "Fill in name field with 'Test'"
   - "Click Submit"
   - "Expect: entity appears in the list with name 'Test'"
3. Identify any setup required (seed data, auth state, etc.)

## Outputs
- URL or route of the surface to test
- Step-by-step spec (actions + expected outcomes)
- Setup requirements (auth state, seed data)

## Gate
None. Planning only.
