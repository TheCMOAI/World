# Blackboard Access Contract

Who can read and write what. This is enforced by convention (`binding.yaml` per
discipline) and by the tool fence: only `read`, `manage`, `run_stage`,
`run_workflow`, and `gate` are available. No raw SQL.

## Read rules

- Any discipline may read from: `entities`, `workspaces`, `workflow_runs`,
  `workflow_steps`, `stage_packets`, `decisions`, `learnings`, `gates`
- A discipline reads its own prior `stage_packets` only (scoped by workspace_id)
- Cross-discipline reads go through the blackboard or workflow packets, not direct imports

## Write rules

- Only `03_execute` stages mutate domain tables. `stage_runtime.py` records
  immutable `stage_packets` for every stage.
- Every discipline declares its `write_surface` in `binding.yaml`
- `entity_activity_log` is append-only — INSERT only, never UPDATE or DELETE
- `decisions` and `learnings` are written by the executing discipline only

## Gate rule

Any action that is irreversible, destructive, externally visible, or spend-affecting
MUST write a gate before the execute stage runs it. The execute stage MUST check
gate resolution before proceeding.

## What the LLM cannot do

- Raw SQL
- Shell commands outside `lib/` scripts
- Read files outside the World folder
- Call external APIs directly (must go through a stage's `run.py` or `lib/exec.py`)
