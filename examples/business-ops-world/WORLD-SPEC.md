# WORLD-SPEC: Business Ops Example

## Domain

A generic service business that turns a customer request into a quoted,
scheduled, and followed-up job.

## Entity

`entity` represents one customer request, job, case, or account. The stencil
keeps this generic so builders can rename it for their own domain.

## Disciplines

| Discipline | Owns | Writes |
|------------|------|--------|
| `ops-intake` | customer/job intake state | `business_artifacts.kind = intake_summary` |
| `ops-quote` | quote follow-up state | `business_artifacts.kind = quote_plan` |
| `ops-schedule` | scheduling state | `business_artifacts.kind = schedule_plan` |
| `ops-followup` | customer follow-up state | `business_artifacts.kind = followup_plan` |

## Workflow

`service-business-ops` runs each discipline through `01_read`, `02_plan`, and
`03_execute`. Each discipline reads the blackboard and writes its own artifact;
later disciplines consume those artifacts through Postgres.
