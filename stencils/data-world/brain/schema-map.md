# Blackboard Schema Map

The blackboard is Postgres. This file documents what each table does, who writes
to it, and who reads from it. Keep this up to date as you add tables.

**Rule:** If a table is not in this map, no discipline should be reading or writing
it. Add it here before you add it to the schema.

---

## Core tables

| table | purpose | writers | readers |
|-------|---------|---------|---------|
| `entities` | the things your World acts on (projects, cases, customers…) | `manage` tool, onboarding | every discipline's `01_read` |
| `workspaces` | a session of work scoped to an entity | session open/close | every stage |
| `workflow_runs` | durable status for a multi-discipline workflow | `lib/workflow_runtime.py` | harness, reporting, resume |
| `workflow_steps` | per-step trace for a workflow run | `lib/workflow_runtime.py` | harness, reporting, resume |
| `stage_packets` | typed data flowing between stages | every stage's `run.py` | the next stage's `run.py` |
| `decisions` | what was decided and why | `03_execute` stages | `01_read` stages (memory) |
| `learnings` | observations and patterns accumulated over time | `03_execute` stages | `01_read` stages (memory) |
| `gates` | human approval gates before irreversible actions | `tools.gate()` | `_shared/gates/gate.py` |
| `entity_activity_log` | append-only history of what happened | `03_execute` stages | reporting, audit |
| `activations` | what the scheduler proposes — which discipline to wake for which entity, and why (migration 002) | `lib/watch.py` | `lib/dispatch.py`, reporting, audit |
| `entity_notes` | tiny default example table for notes attached to an entity | `example-notes/03_execute` | `example-notes/01_read` |
| `business_artifacts` | runnable generic business-ops artifacts flowing across disciplines | `ops-*/03_execute` | `ops-*/01_read`, workflows, audit |

---

## Domain-specific tables

Add your World's tables here as you build out disciplines.

| table | purpose | writers | readers |
|-------|---------|---------|---------|
| *(your table)* | *(what it does)* | *(what writes)* | *(what reads)* |

---

## Schema rules

1. Every table has `id` (UUID), `created_at` (TIMESTAMPTZ).
2. Mutable rows add `updated_at` (TIMESTAMPTZ).
3. Append-only logs (like `entity_activity_log`) never update rows.
4. JSON blobs go in JSONB columns.
5. Status columns use TEXT with a documented value set (not enums — easier to extend).
