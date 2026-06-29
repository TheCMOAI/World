# BUILD.md — How to Build a World

You are an AI agent. An operator has given you a domain and asked you to build a
World for it using this stencil. Read this document fully before writing a single
file. It tells you what to build, in what order, the rules, and exactly where
you will get stuck.

**Don't have a clear domain yet?** Stop and run `DISCOVER.md` first — it
interviews the operator and produces a `WORLD-SPEC.md`. If you already have a
`WORLD-SPEC.md`, use it: it answers Step 0 below, names the entity, and defines
the first discipline to build. Build that **one** discipline end to end before any
other.

---

## What you are building

A **World** is a structured folder an LLM lives and operates inside. It has:

- **Disciplines** — independent units of work, each owning one job
- **A blackboard** — a Postgres database that is the only source of truth
- **A harness** — a thin runtime that dispatches the LLM's tool calls to the right discipline and stage
- **An agent.md** — the document the LLM reads to orient itself to the domain

Your job is to take this blank stencil and fill it in for the operator's domain.
You replace placeholder text, copy and rename templates, write real stage logic,
and extend the schema. You do not change the architecture — only the content.

---

## What this stencil gives you and what it does not

Read this before you start. It will save you from building the wrong thing.

### What you get

- The complete folder architecture (ICM layout, discipline structure, stage pattern)
- A working blackboard read/write layer (`lib/_shared/db/`)
- A stage dispatcher (`lib/stage_runtime.py`) that routes `run_stage` calls
- A workflow runner (`lib/workflow_runtime.py`) that runs multi-discipline YAML workflows
- The gate pattern (`lib/_shared/gates/`) for human approval before mutations
- A core Postgres schema (entities, workspaces, stage packets, decisions, gates)
- A blank discipline with all three stages stubbed out and documented
- A blank workflow template and a runnable service-business operations workflow
- A scheduler (the activation layer) so disciplines can wake themselves on
  blackboard conditions — `lib/watch.py` proposes work, `lib/dispatch.py` opens it
  (migration 002, `brain/activation-model.md`)

### What you do NOT get and must build yourself

**1. Tool registration with your LLM.**
`lib/tools.py` defines the five tool functions (`run_stage`, `run_workflow`, `read`, `manage`, `gate`)
as Python. It does NOT register them with any LLM. You must wire these into your
LLM's tool calling API — Claude's `tools` parameter, OpenAI's `function_calling`,
Codex's tools interface, or whatever harness you are using. See "Wiring tools.py"
below. This is the most critical step and the one most likely to be skipped.

**2. A gate resolution interface.**
When a stage calls `gate()`, it writes a row to the `gates` table with `status: open`
and stops. There is nothing in this stencil that surfaces that gate to the operator
or lets them resolve it. You need to build something — a CLI command, a simple UI,
or a chat message that says "gate open, reply to proceed." Without this, gated
actions are permanently blocked.

**3. A workflow UI.**
`lib/workflow_runtime.py` can execute workflow YAML and record workflow rows, but
there is no polished UI for inspecting, approving, or resuming workflow runs. Use
the CLI or harness tool until you build a product surface.

**4. A discipline map for the operating LLM.**
The LLM operating the World needs to know what disciplines exist and what they do.
There is no auto-generated discipline map. If you have five disciplines, the LLM
will not know about them unless you either: (a) inject the discipline list into the
system prompt, or (b) point the LLM at a hand-maintained `DISCIPLINES.md` file that
lists what is available. Build this alongside your disciplines or the operating LLM
will not activate them.

**5. Real stage logic.**
The `run.py` files in `_template` are working stubs. They read from and write to
the blackboard correctly. But the actual domain logic — what your discipline reads,
how it plans, what it executes — requires knowledge only the operator has. Expect
to write the first version of each stage, show the operator what it produces, and
iterate. The stencil cannot know your domain.

**6. External integrations.**
If your disciplines need to call external APIs (send emails, pull from a SaaS,
write to a CRM), the `exec.py` layer is where that code lives. The stencil cannot
implement these for you. They are real engineering — auth, rate limits, error
handling, pagination. Budget time for them.

**7. Error recovery and retries.**
If an execute stage fails halfway through, there is no recovery path in the stencil.
The `stage_packets` table records what ran, but there is no automatic retry or
rollback. Build idempotency into your execute stages from the start: check whether
an action already succeeded before running it again.

---

## Prerequisites — what you need before starting

```
Postgres 14+        running locally or remotely
                    Fastest local option: docker run -e POSTGRES_PASSWORD=world \
                      -p 5432:5432 postgres:16

Python 3.11+        for running stage scripts

psycopg2            pip install psycopg2-binary

DATABASE_URL        export DATABASE_URL=postgresql://postgres:world@localhost:5432/world

An LLM harness      Claude Code, Codex, or a custom tool-calling setup.
                    The harness must support tool/function calling — agent.md alone
                    is not enough. See "Wiring tools.py" below.
```

If you are missing any of these, stop and get them before building the World.

---

## Wiring tools.py to your LLM

This is the step most builders skip. `tools.py` defines what the LLM can do.
Without wiring, the LLM has no tools and the World is a folder of docs.

### Claude Code / CLAUDE.md approach

If the operating LLM is Claude Code, put `agent.md` content into `CLAUDE.md` at
the World root. Claude Code reads CLAUDE.md as its system context. For tools, use
Claude Code's `allowed_tools` and bash tool to call `stage_runtime.py` directly:

```bash
# The LLM calls this as a bash command:
python lib/stage_runtime.py --discipline case-research --stage 01_read \
  --args '{"entity_id": "abc", "workspace_id": "xyz"}'
```

This is the lowest-friction path. Claude Code's bash tool IS your tool interface.
You do not need to register tools — stages are just Python scripts the LLM runs.

### Claude API / custom harness approach

If you are building a custom harness, register the tools from `tools.py` as Claude
tool definitions:

```python
tools = [
    {
        "name": "run_stage",
        "description": "Activate a stage in a discipline",
        "input_schema": {
            "type": "object",
            "properties": {
                "discipline": {"type": "string"},
                "stage": {"type": "string"},
                "args": {"type": "object"}
            },
            "required": ["discipline", "stage", "args"]
        }
    },
    # repeat for read, manage, gate
]
```

Then in your tool execution handler, dispatch to the matching function in `tools.py`.

### OpenAI / Codex approach

Same pattern as above but using the `functions` or `tools` parameter in the
OpenAI API. The function bodies in `tools.py` are the handlers — call them when
the model returns a `tool_calls` result.

**The golden rule:** the LLM must be able to call `run_stage`, `read`, `manage`,
and `gate` as real tool calls — not by writing Python or SQL in the chat. If it
cannot, the World is not wired.

---

## Step 0 — Understand the domain before touching any file

If you ran `DISCOVER.md`, these answers are already in `WORLD-SPEC.md` — read it
and skip to Step 1. Otherwise, answer these questions before writing anything:

1. **What is the entity?** The central thing this World acts on behalf of.
   A legal case. A customer. A research project. A job candidate. A product launch.
   This word replaces "entity" everywhere in the stencil.

2. **What are the jobs?** The distinct things this World does.
   Each job becomes a discipline. Keep the list short — three to five disciplines
   for a first version. You can add more later. Examples for a legal World:
   - `case-research` — find relevant precedents and statutes
   - `document-review` — analyze documents for a case
   - `brief-drafting` — produce legal briefs

3. **What does each job produce?** A discipline must have a concrete deliverable.
   "Research findings written to the blackboard" is a deliverable.
   "Help with legal stuff" is not.

4. **What does the World need to remember?** What tables beyond the core schema
   does this domain need? What does the LLM need to know at the start of every
   session that it cannot derive from the conversation?

5. **What requires operator approval?** What actions are irreversible, destructive,
   or externally visible? These get gates. Start with a short list — you can add
   gates later. Missing a gate is safer to add than removing one that was wrong.

Write your answers as a comment block at the top of `agent.md` before you write
anything else.

---

## Step 1 — Update agent.md

`agent.md` is the entry point. The operating LLM reads it to inhabit the World.

Replace the placeholder preamble (everything before the first `---`) with your
domain identity. Write in second person, present tense:

```
You are a legal research operator. You manage case research, document review, and
brief drafting for law firms. Your entities are cases. Your operators are attorneys
and paralegals. You have real judgment about legal strategy — you push back when an
approach has weak precedent, and you flag ambiguity in statutes before acting.
```

**Also add a discipline list** to agent.md. The operating LLM will not know
what disciplines exist unless you tell it:

```markdown
## Available disciplines

- `case-research` — find precedents and statutes relevant to a case
- `document-review` — analyze documents for findings and risks
- `brief-drafting` — produce legal briefs from research findings
```

This is your discipline map. Keep it updated as you add disciplines.

Do not change anything below the first `---` in agent.md. The tools section and
rules are the harness contract — they apply to every World.

Rename `entity` to your entity type throughout the operator-facing text.
Do not leave "entity" in any text the operator will see.

---

## Step 2 — Rename the entity in the schema

Open `migrations/001_init.sql`. The `entities` table is the core of your World.

**Option A (simple):** Keep the table named `entities`. Add domain-specific columns
to the `metadata JSONB` field. Good for simple domains or first versions.

**Option B (explicit):** Rename to your entity type (`cases`, `projects`, etc.).
Then update every reference to `entities` in:
- `lib/_shared/db/read.py`
- `lib/tools.py` (the `manage` tool)
- `disciplines/_template/stages/01_read/run.py`

Option A ships faster. Option B is cleaner for domains with 10+ entity-specific
fields. Start with A and migrate to B if you need it.

Add domain-specific columns. For a legal World:

```sql
ALTER TABLE entities ADD COLUMN jurisdiction TEXT;
ALTER TABLE entities ADD COLUMN case_type TEXT;
ALTER TABLE entities ADD COLUMN filed_at TIMESTAMPTZ;
ALTER TABLE entities ADD COLUMN opposing_counsel TEXT;
```

---

## Step 3 — Build your disciplines

For each job from Step 0, create a discipline:

```bash
cp -r disciplines/_template disciplines/<your-discipline-name>
```

Name disciplines in `kebab-case`. Noun or short noun phrase — the job, not the
action. `case-research`, not `do-case-research`.

Build one discipline fully before starting the next. A half-built discipline that
cannot run its `01_read` stage is worth less than no discipline at all.

### 3a. Write CONTEXT.md (the stage router)

This is the first file the operating LLM reads when it enters this discipline.
Make it precise:
- What this discipline does (one sentence)
- Which stage handles which kind of request (the stage map table)
- What tables it writes to
- What it must not touch

If this file is vague, the operating LLM will make wrong choices about which stage
to run. Be specific.

### 3b. Fill in binding.yaml

Set `model_tier`:
- `worker` — focused single-stage tasks. Most disciplines.
- `orchestrator` — multi-stage coordination or calling sub-disciplines.
- `router` — lightweight routing only, no execution.

Add tables this discipline writes to under `write_surface:`.
The operating harness uses this to enforce write permissions.

### 3c. Write the stages

Each stage has two files: `CONTEXT.md` (the contract) and `run.py` (the implementation).

**Stage 01 — Read. No domain mutations.**

Pull current state from the blackboard. Return a state packet. Nothing else.
`lib/stage_runtime.py` records the returned packet in `stage_packets`; the stage
itself should not write domain tables.

Common mistake: pulling too much data. Read only what this discipline needs for its
planning stage. If you find yourself joining five tables, the discipline is probably
trying to do too much.

In `stages/01_read/run.py`:
- Replace placeholder reads with your real blackboard reads
- Add external source reads to `lib/exec.py` and call them here
- Return a complete state packet — gaps are flagged in `data_gaps`, not silenced

**Stage 02 — Plan. No domain mutations.**

Read the state packet. Apply domain logic. Return a typed plan with proposed actions.
`lib/stage_runtime.py` records the returned plan packet in `stage_packets`.

This is the hardest stage to write because it requires the most domain knowledge.
The plan must be specific enough that execute can act on it without guessing.
Vague plans ("do some research") produce vague execution. Each action needs a type,
a description, and a payload that execute can act on directly.

Gotcha: the LLM building this stage will write placeholder action types. You need
to define the real action types for your domain and implement handlers for each
in the execute stage before the plan stage is useful.

**Stage 03 — Execute. The only mutation stage.**

Act on the plan. Write outcomes back. Check gates before gated actions.

In `stages/03_execute/run.py`:
- Implement a handler for each action type defined in the plan stage
- After each action: write to `entity_activity_log` and `decisions`
- Always verify the write landed before reporting success
- If a gate is unresolved, skip the action and report it — do not error out

Gotcha: the execute stage is where real integrations live. If your discipline needs
to call an external API, that call goes in `lib/exec.py` and the execute stage calls
it. This is real code — you cannot stub it and call the discipline done.

**Stage CONTEXT.md files**

Write real contracts for each stage — not the placeholder headings. The operating
LLM reads these to understand what a stage accepts and produces. A CONTEXT.md that
still says `<describe inputs>` is a broken stage contract.

### 3d. Define your action types

Between plan and execute, you need a defined vocabulary of action types. Write them
down in `disciplines/<name>/references/action-types.md`:

```markdown
## Action types

| type | description | reversible | requires_gate |
|------|-------------|------------|---------------|
| save_finding | write a research finding to the blackboard | yes | no |
| tag_precedent | tag a case as a relevant precedent | yes | no |
| archive_case | set case status to archived | no | yes |
```

The plan stage proposes these types. The execute stage handles them. If the two
disagree, the execute stage will skip unknown action types. Document them.

### 3e. Add references/

Frozen domain knowledge goes here — rules, conventions, catalogs, playbooks.
The stage reads from these files; it does not hardcode the knowledge.

Examples:
- `legal-standards.md` — accepted brief formats
- `jurisdiction-rules.yaml` — what varies by jurisdiction

---

## Step 4 — Extend the schema

Add tables your disciplines need to `migrations/001_init.sql`.

Rules:
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` on every table
- `created_at TIMESTAMPTZ DEFAULT NOW()` on every table
- `updated_at TIMESTAMPTZ DEFAULT NOW()` on mutable tables
- Append-only logs never get `updated_at`
- JSONB for payloads, TEXT for strings (no VARCHAR limits)
- Status columns: TEXT, values documented in `brain/schema-map.md`

After every table you add, add a row to `brain/schema-map.md`. If it is not in
the schema map, the operating LLM cannot reason about it.

---

## Step 5 — Build a minimal gate resolution path

You built a gate pattern. Now build the minimum needed to resolve one.

The simplest thing that works: a CLI script in `lib/`:

```bash
python lib/resolve_gate.py --gate-id <id> --answer "approved"
```

Without this, the first time a stage gates an action, the operator has nowhere to
go. Build it before you build the second discipline.

---

## Step 5b — Make disciplines wake themselves (the scheduler)

Optional, but it is what turns a reactive World into an autonomous one. Skip it
for a first build; add it the moment you want the World to act without an operator
typing a request (follow up a stale customer request, reorder low stock, chase an overdue task).

1. Run the migration: `psql $DATABASE_URL < migrations/002_activation.sql`
2. In a discipline's `binding.yaml`, set its `activation` block to `mode: condition`
   and write a read-only SELECT that returns the `entity_id`s that should wake it.
3. Run the loop:

```bash
python lib/watch.py --once --dry-run   # which entities would fire, and why
python lib/watch.py --once             # propose them onto the blackboard
python lib/dispatch.py --once          # open each discipline's read stage
```

4. In production, run `watch.py --once` and `dispatch.py --once` on a timer (cron
   or launchd), not `--loop`.

The scheduler **senses and opens; it never plans or executes on its own.** Dispatch
runs only the read stage — mutations stay behind read → plan → execute and its
gates. High-risk activations open a gate before any work begins. Read
`brain/activation-model.md` before you wire a condition that touches money,
inventory counts, or anything externally visible.

---

## Step 6 — Update config.yaml

Set `world.name`. Leave `database.url` as `${DATABASE_URL}`.

---

## Step 7 — Verify your World

**Before calling any discipline done:**
- [ ] `01_read` runs without errors and returns a real state packet (not placeholder data)
- [ ] `02_plan` reads that packet and returns a plan with at least one real action type
- [ ] `03_execute` handles that action type, writes to the blackboard, and returns a result
- [ ] The result is visible in the DB (`SELECT * FROM entity_activity_log`)

**Before calling the World done:**
- [ ] `agent.md` has no placeholder text
- [ ] `agent.md` lists all available disciplines
- [ ] Every discipline's `CONTEXT.md` has real content (not `<placeholders>`)
- [ ] Every stage's `CONTEXT.md` has real inputs, process, outputs, and gate conditions
- [ ] Every domain table is in `migrations/001_init.sql` and `brain/schema-map.md`
- [ ] There is a path for the operator to resolve a gate
- [ ] `tools.py` is wired to the LLM harness — confirmed by making a real tool call

**Gate check:**
- [ ] Every irreversible action has `requires_gate: true`
- [ ] Every external mutation (email, API write, third-party system) is gated

---

## Known shortcomings in the current stencil

These are real gaps. They are not bugs — they are design decisions to keep the
stencil minimal. You will hit them. Plan for them.

**No workflow UI.** `workflows/` now run through `lib/workflow_runtime.py`, but
the stencil still has no dashboard for workflow history, gates, or resume actions.

**No context-window management.** Once you have 6+ disciplines, the operating LLM
cannot read all their CONTEXT.md files in one turn. You will need a routing layer —
either a lightweight router discipline that reads the discipline list and picks the
right one, or a toolbelt map injected into the system prompt. The discipline list
in `agent.md` is a stop-gap. Build a real router when the World grows.

**No multi-user or auth.** The stencil has one operator and one entity namespace.
If you need multiple users, user-scoped entity access, or role-based permissions,
add a `users` table and scope every query by `user_id`. The stencil does not do this.

**psycopg2 is synchronous.** If you are building on an async framework (FastAPI,
etc.), replace psycopg2 with asyncpg and rewrite `read.py` and `write.py` as async.

**No retry or partial recovery.** If an execute stage fails after completing two of
five actions, there is no checkpoint. The stencil writes to `entity_activity_log`
after each action, so you can query what completed — but there is no automatic
resume. Build idempotency into each action handler: check whether it already ran
before running it again.

**Stage packets accumulate without cleanup.** `stage_packets` grows indefinitely.
For production, add a cleanup job that deletes packets older than N days for
completed workspaces.

---

## What you must not change

1. **The tool fence.** The LLM calls only `run_stage`, `run_workflow`, `read`, `manage`, `gate`.
   Do not add raw SQL tools, file write tools, or shell execution tools.

2. **The packet flow.** Stages communicate via `stage_packets` in the blackboard,
   not in memory, not in files, not via direct return values.

3. **Read/plan/execute separation.** Stages 01 and 02 never mutate domain tables.
   Runtime-owned `stage_packets` writes are the only exception. Stage 03 never plans.
   Never collapse this.

4. **Blackboard as source of truth.** If a file and the DB disagree, the DB wins.

5. **Gates before mutations.** A gated action that runs without gate resolution is
   a bug. Never skip the gate check.

6. **No cross-discipline imports.** A discipline imports only from its own `lib/`
   and `lib/_shared/`. Never from another discipline.

---

## Common mistakes

**Building five disciplines before testing one.** Build one discipline end-to-end
(read → plan → execute → verify in the DB) before starting the next. Broad-first
building produces five broken disciplines instead of one working one.

**Writing placeholder action types.** If your plan stage proposes `action_type:
"do_the_thing"` and your execute stage has no handler for it, nothing runs. Define
real action types with real handlers before calling a discipline done.

**Skipping CONTEXT.md files.** The operating LLM reads these. Blank or placeholder
CONTEXT.md files mean the LLM cannot reason about what a stage accepts or produces.
Fill them in.

**Not wiring tools.** See "Wiring tools.py" above. If the operating LLM cannot
call `run_stage` as a real tool, the World is a folder of docs.

**Over-gating.** Gate only actions that are truly irreversible or externally
visible. A gate on every action creates an unusable World.

**Putting external API calls in the plan stage.** Plan is read-only. If you need
fresh external data, pull it in `01_read` and store it in the state packet.

---

## Handing off to the operator

When the World is built and verified:

1. `psql $DATABASE_URL < migrations/001_init.sql`
2. `export DATABASE_URL=postgresql://...`
3. Wire `agent.md` into the operating LLM's system prompt or CLAUDE.md
4. Wire `tools.py` into the LLM's tool calling interface
5. Confirm the LLM can call `run_stage` and get a real result

The operator should be able to give one plain-language instruction and get a real
result backed by discipline logic and blackboard state. If it takes more than one
instruction to activate a discipline, the routing in `agent.md` needs work.
