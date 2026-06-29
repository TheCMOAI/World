# Disciplines

This file is injected into the operating LLM's context alongside agent.md.
Update it whenever you add, rename, or remove a discipline.
Keep it current — the operating LLM uses this to know what work is available.

---

## Available disciplines

| discipline       | job                                                        | entry stage |
|------------------|------------------------------------------------------------|-------------|
| example-notes    | create, summarize, and retrieve notes attached to an entity | `01_read`   |
| ops-intake       | turn an incoming customer or job request into intake state | `01_read`   |
| ops-quote        | turn intake state into a quote follow-up plan              | `01_read`   |
| ops-schedule     | turn quote state into a scheduling plan                    | `01_read`   |
| ops-followup     | turn scheduling state into a customer follow-up plan       | `01_read`   |

---

## How to activate a discipline

Call `run_stage` with the discipline name and stage for single-discipline work.
Call `run_workflow` when the request naturally spans several disciplines. Always
read the entity from the blackboard first to confirm it exists. The harness gives
you a `workspace_id` in the turn context; include it in every direct stage call.

```
# confirm the entity exists
read("entities", filter={"name": "Acme Corp"})

# run from the beginning
run_stage("example-notes", "01_read", {"entity_id": "<uuid>", "workspace_id": "<workspace_uuid>"})

# run a specific stage
run_stage("example-notes", "02_plan", {
  "entity_id": "<uuid>",
  "workspace_id": "<workspace_uuid>",
  "intent": "create_note",
  "content": "Customer prefers email follow-up."
})

# run the full generic business-ops worked example
run_workflow("service-business-ops", "<uuid>", inputs={
  "objective": "Move a service request through intake, quote, schedule, and follow-up."
})
```

## Available workflows

| workflow | job |
|----------|-----|
| example-notes | create one note through read, plan, execute |
| service-business-ops | run intake -> quote -> schedule -> follow-up for one service request |

---

## Discipline selection rules

- Match the operator's intent to the discipline's job description above.
- If no discipline matches, say so — do not improvise outside the discipline boundary.
- If multiple disciplines apply, prefer a workflow. If no workflow exists, run stages in order.
- Never jump to `03_execute` without running `01_read` and `02_plan` first in the same session.

---

## Adding a discipline

1. Copy `disciplines/_template/` to `disciplines/<your-discipline>/`
2. Fill in the CONTEXT.md, binding.yaml, and stage run.py files
3. Add a row to the table above
4. Run `python lib/world_doctor.py` — it will verify the structure

---

## Autonomous activation

A discipline can wake itself instead of waiting for an operator request. Set its
`activation` block in `binding.yaml` to `mode: condition` with a read-only query,
then run the scheduler (`lib/watch.py` + `lib/dispatch.py`). The scheduler opens
the discipline's read stage; you still decide whether to act. Full model:
`brain/activation-model.md`.
