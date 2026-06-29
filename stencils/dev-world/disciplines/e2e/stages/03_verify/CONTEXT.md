# e2e / 03_verify

**Job:** Verdict. Did the feature work as expected in the real UI?

## Inputs
- Step results from `02_drive`

## Process
1. Review pass/fail per step
2. Classify each failure:
   - **Feature broken** — the code change did not produce the expected UI behavior
   - **Test brittle** — the spec targeted the wrong selector or assumed wrong state
   - **Environment** — the app was not running, DB was empty, auth expired
3. Write the verdict

## Outputs

```
E2E VERDICT: PASS | FAIL | ENVIRONMENT

N steps passed · M steps failed

Failures:
  Step 3 — "Click Submit" — FAIL
    Expected: entity appears in list
    Actual: 500 error response
    Classification: feature broken
    Screenshot: e2e/screenshots/step3-fail.png

Action: route to debug / 01_reproduce for the 500 error
```

## Verdict rules

| condition                          | verdict      | action                              |
|------------------------------------|--------------|-------------------------------------|
| all steps pass                     | PASS         | feature verified in real UI         |
| steps fail due to feature code     | FAIL         | route to debug discipline           |
| steps fail due to brittle selectors | FAIL (brittle) | fix the spec, re-run from 02_drive |
| app not running / unreachable      | ENVIRONMENT  | fix environment, re-run from 02_drive |

## Done when
Verdict written with classification for every failure. PASS = shippable.
FAIL = route to debug. ENVIRONMENT = fix environment first.
