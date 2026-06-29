# ops-followup - Stage Router

**Job:** Turn scheduling state into a customer follow-up plan.

## Stage map

| request kind | entry stage | runs through |
|--------------|-------------|--------------|
| plan customer follow-up | `01_read` | 01 -> 02 -> 03 |

## Owns

- Writes `business_artifacts.kind = followup_plan`
- Requires a `schedule_plan` artifact

