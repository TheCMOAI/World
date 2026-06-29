# e2e / 02_drive

**Job:** Execute the spec against the real running application with Playwright.
Capture a pass/fail result for each step.

## Inputs
- Spec from `01_target`
- `E2E_BASE_URL` — the app's base URL (default: `http://localhost:3000`)

## Process
1. Confirm the app is running (curl or fetch the base URL)
2. Launch Playwright (headless by default, headed with `--headed` for debugging)
3. Execute each step in the spec in order
4. For each step: record whether it passed, failed, or errored
5. On failure: capture a screenshot and the error message
6. Complete all steps even if one fails — collect the full picture

## Outputs
- Per-step result: step description, status (pass/fail/error), error if any
- Screenshot paths for any failed steps
- Overall: N passed, M failed

## Gate
None. Driving only. Verdict is in `03_verify`.

## Debugging a failing step
- Run with `--headed` to watch Playwright navigate
- Check the app's console for errors (`browser_console_messages`)
- Confirm the selector targets the right element (IDs are more stable than text)
