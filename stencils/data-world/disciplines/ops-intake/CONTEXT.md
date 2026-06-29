# ops-intake - Stage Router

**Job:** Turn a customer or job entity into an intake summary.

## Stage map

| request kind | entry stage | runs through |
|--------------|-------------|--------------|
| summarize incoming work | `01_read` | 01 -> 02 -> 03 |

## Owns

- Writes `business_artifacts.kind = intake_summary`
- Reads the entity and prior business artifacts from the blackboard

