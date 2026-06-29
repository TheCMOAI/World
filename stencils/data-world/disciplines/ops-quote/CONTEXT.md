# ops-quote - Stage Router

**Job:** Turn intake state into a quote follow-up plan.

## Stage map

| request kind | entry stage | runs through |
|--------------|-------------|--------------|
| plan quote follow-up | `01_read` | 01 -> 02 -> 03 |

## Owns

- Writes `business_artifacts.kind = quote_plan`
- Requires an `intake_summary` artifact

