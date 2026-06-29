# e2e — Stage Router

**Job:** Verify a change works in the real running application via browser automation.
Use this after `feature` or `debug` when the change has a visible UI surface.
Optional — only needed if your World has a web UI and Playwright is available.

## Requirements
- Playwright installed: `pip install playwright && playwright install chromium`
- Application running (or startable via a command)
- Set `E2E_BASE_URL` to the app's URL (default: `http://localhost:3000`)

## Stage map

| the task is…                          | entry stage  | runs through  |
|---------------------------------------|--------------|---------------|
| full e2e from scratch                 | `01_target`  | 01 → 02 → 03  |
| spec written, need to drive + verify  | `02_drive`   | 02 → 03       |
| already driven, need verdict only     | `03_verify`  | 03 only       |

## Stages

```
stages/
  01_target/   identify the UI surface affected by the change; write the spec
  02_drive/    run Playwright against the real app; capture pass/fail per step
  03_verify/   verdict — did the feature work as expected in the real UI?
```

## Law

- `02_drive` never mocks the backend. It hits the real running app.
- If the app is not running, start it before this stage — do not skip the stage.
- A passing e2e does not replace unit tests. Both run. e2e is the integration
  confidence check; unit tests catch regressions faster.
