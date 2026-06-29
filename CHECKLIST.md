# World Readiness Checklist

Use this before calling a World "done." Run through it in order.
A World is not ready until every item is checked.

---

## data-world checklist

### Environment
- [ ] `DATABASE_URL` set in environment
- [ ] `pip install psycopg2-binary` done
- [ ] `psql $DATABASE_URL < migrations/001_init.sql` run
- [ ] `python lib/world_doctor.py` returns exit 0

### agent.md
- [ ] Placeholder preamble replaced with real domain identity
- [ ] "entity" renamed to your entity type throughout
- [ ] Available disciplines listed under `## Available disciplines`
- [ ] No `<placeholder>` text remaining anywhere in the file

### Schema
- [ ] Every domain table added to `migrations/001_init.sql`
- [ ] Every domain table documented in `brain/schema-map.md` (purpose, writers, readers)
- [ ] Tables have `id UUID`, `created_at`, and `updated_at` where applicable
- [ ] Append-only tables (activity logs) have no `updated_at`

### Disciplines
For each discipline (repeat per discipline):
- [ ] `CONTEXT.md` — real content, no placeholders, stage map is accurate
- [ ] `binding.yaml` — `model_tier` set, `write_surface` lists real tables
- [ ] `stages/01_read/CONTEXT.md` — real inputs/outputs documented
- [ ] `stages/01_read/run.py` — reads from real tables, returns real state packet
- [ ] `stages/02_plan/CONTEXT.md` — real action types documented
- [ ] `stages/02_plan/run.py` — produces real typed actions, writes packet to DB
- [ ] `stages/03_execute/CONTEXT.md` — gate conditions documented
- [ ] `stages/03_execute/run.py` — handler for every action type, verifies writes
- [ ] At least one end-to-end test: run 01 → 02 → 03, check `entity_activity_log`

### Logic invariants
- [ ] No `01_read` or `02_plan` stage writes to the database
- [ ] Every `03_execute` stage verifies writes before reporting success
- [ ] Every gated action has `requires_gate: true` in the plan packet
- [ ] No discipline imports from another discipline's code
- [ ] All external API calls are in `lib/exec.py`, not in stage `run.py` files

### Gate path
- [ ] At least one path exists for the operator to resolve an open gate
  (CLI script, message, or UI — doesn't matter, but it must exist)

### Tools wiring
- [ ] LLM can call `run_stage` and get a real result back
- [ ] Harness opens a workspace and injects `workspace_id` into the turn context
- [ ] `run_workflow` can execute `workflows/example-notes.yaml`
- [ ] `service-business-ops` workflow writes `intake_summary`, `quote_plan`, `schedule_plan`, and `followup_plan`
- [ ] LLM can call `read` and get rows from the DB
- [ ] LLM can call `manage entity.create` and see the entity in the DB
- [ ] LLM can call `gate` and see the row in the `gates` table

---

## dev-world checklist

### Setup
- [ ] Python 3.11+ available
- [ ] `tests/` directory exists with at least one test file
- [ ] `python lib/run_tests.py` runs without collection errors
- [ ] `python lib/commit_gate.py --update-baseline` run to set initial baseline
- [ ] `lib/.test_baseline.json` committed to git

### CLAUDE.md
- [ ] Domain preamble is accurate for this codebase
- [ ] `## Available disciplines` list matches actual disciplines folder
- [ ] Naming law is documented (stage folders `NN_verb`, disciplines kebab-case)
- [ ] No placeholder text remaining

### Disciplines
For each real discipline added (debug/feature/refactor/review/test are the defaults):
- [ ] `CONTEXT.md` — one-sentence job description is specific to this codebase
- [ ] Stage map table is accurate (entry stages correct for this domain)
- [ ] `binding.yaml` present

### Lib tools
- [ ] `python lib/run_tests.py` scopes to correct tests directory
- [ ] `python lib/who_calls.py <symbol>` returns results from this codebase
- [ ] `python lib/commit_gate.py` blocks correctly on new failures
- [ ] `python lib/ringer.py --backend-only` exits 0 on a clean codebase

### Ringer
- [ ] `python lib/ringer.py --intent "test run"` completes without errors
- [ ] Verdict report written to `workspaces/ringer/`
- [ ] `lib/review_diff.py` has `REVIEW_CMD` set or documented

---

## Both worlds — final check

- [ ] No file in the stencil still contains `<placeholder>` text
- [ ] README updated if you renamed entities, disciplines, or tools
- [ ] At least one real operator interaction tested end-to-end
  - data-world: "Create an entity and add a note to it"
  - dev-world: "Fix a bug in this codebase" runs debug discipline through 04_verify
