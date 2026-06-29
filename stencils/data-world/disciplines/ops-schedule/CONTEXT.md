# ops-schedule - Stage Router

**Job:** Turn quote state into a scheduling plan.

## Stage map

| request kind | entry stage | runs through |
|--------------|-------------|--------------|
| plan scheduling | `01_read` | 01 -> 02 -> 03 |

## Owns

- Writes `business_artifacts.kind = schedule_plan`
- Requires a `quote_plan` artifact

