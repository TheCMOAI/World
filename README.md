# World

A blank stencil for building an AI operating domain.

Download the stencil that matches your use case, fill in your disciplines, point
an LLM at the orientation file, and you have a working World — a structured domain
an AI agent can actually inhabit and operate inside.

---

## Two flavors

```
stencils/
  data-world/    ICM + Postgres blackboard + Hearsay-II disciplines
                 Use when: your World acts on data — customers, cases, tickets,
                 projects, anything with persistent state in a database.

  dev-world/     ICM + filesystem blackboard + 5-phase discipline loop
                 Use when: your World acts on a codebase — bugs, features,
                 refactors, reviews, test suites.
```

They share the same architectural spine. They differ in what the **blackboard** is.

---

## What is a World?

A World is a folder an LLM lives inside. It knows the rules of the domain, the
tools available, where knowledge lives, and what work looks like. The LLM is not
a chatbot making API calls from the outside. It IS the operator — reading from a
shared blackboard, activating disciplines, running stages, and writing outcomes back.

Three architectures combine to make this work:

---

### 1. ICM — Intelligent Control Module (folder structure)

Every folder IS its job. You navigate to the work by navigating the folder. A
discipline folder contains everything needed to do one job: stages, shared scripts,
references, and a router document. You do not need to read anything outside that
folder to understand what it does.

```
disciplines/
  customer-research/    ← one job
    stages/             ← ordered execution
    lib/                ← deterministic scripts, no AI
    references/         ← frozen knowledge the discipline reads
```

**Rule: one folder = one job. Descend for detail, never sideways.**

---

### 2. Blackboard — shared state the LLM reads before acting

The blackboard is the single source of truth. The LLM reads from it before acting,
writes outcomes back after. No state lives in memory between turns.

In a **data-world**: the blackboard is Postgres. State is rows. Disciplines read
tables and write outcomes back.

In a **dev-world**: the blackboard is the codebase — files, git history, test
results. State IS the code. Disciplines read files and write by editing them.

**Rule: read the blackboard before you assert. Write back after you act.**

---

### 3. Hearsay-II — Disciplines as knowledge sources

Each discipline is an independent knowledge source. It activates when its conditions
are met — not when called by a central broker. There is no orchestrator routing
requests through a flowchart. The LLM reads the situation, sees which discipline
applies, and activates it directly.

**Rule: disciplines activate opportunistically. No central broker.**

---

### 4. The scheduler — disciplines that wake themselves

Hearsay-II's third part is the **scheduler**: the control that decides which
knowledge source acts next from the state of the blackboard. Without it a World
is *reactive* — it only moves when an operator types a request. With it a World
is *autonomous* — a discipline wakes itself when its condition is met (a customer
request goes 7 days cold, stock crosses a threshold, a task runs overdue).

There is still no central broker. Each discipline declares its *own* activation
condition; the watcher just evaluates them and lets disciplines self-select.

```
watch.py    senses the blackboard, proposes work onto it
dispatch.py opens the discipline's read stage for each proposal
```

The scheduler senses and opens — it never plans or mutates. Execution stays
behind read → plan → execute and its gates. See
`stencils/data-world/brain/activation-model.md`.

**Rule: the scheduler decides what deserves attention. It does not decide to act.**

---

## Which stencil do you need?

| your World acts on…               | use             |
|------------------------------------|-----------------|
| customers, cases, requests, tickets | `data-world`    |
| projects, documents, records       | `data-world`    |
| a codebase — bugs, features        | `dev-world`     |
| a software repo's quality process  | `dev-world`     |
| something else entirely            | start with `data-world`, the patterns are more general |

---

## How to build your World

Two steps, both LLM-native — you run them inside Claude Code, Cowork, or ChatGPT.

1. **Don't know what to build yet?** Open `DISCOVER.md`. It runs a plain-language
   interview about your business — no jargon, no architecture — and hands you a
   filled `WORLD-SPEC.md`. See `WORLD-SPEC.example.md` for what that looks like.

2. **Have a spec (or a clear domain)?** Open `BUILD.md`. It's written for the LLM
   that will build the World. Point Claude Code or Codex at it with your
   `WORLD-SPEC.md` and it walks through every step.

`DISCOVER.md` → `WORLD-SPEC.md` → `BUILD.md` → a working World.

A generic worked example lives in `examples/business-ops-world/`. Run
`workflows/service-business-ops.yaml` from the data-world stencil to watch
separate disciplines communicate through Postgres in a neutral operations domain.

The `data-world` stencil also includes a small API harness. It opens a workspace
for the session, injects the current blackboard context into each turn, exposes
only the five World tools (`run_stage`, `run_workflow`, `read`, `manage`, `gate`), and has thin
Anthropic/OpenAI adapters over one shared `lib/harness_core.py`.

---

## Repo map

```
World/
  README.md          ← you are here
  DISCOVER.md        ← LLM-run interview: figure out what World to build (start here)
  WORLD-SPEC.example.md  ← what DISCOVER.md produces (a worked plumbing example)
  examples/business-ops-world/ ← generic runnable business-ops worked example
  BUILD.md           ← how to build a World from a spec (LLM-readable instruction set)

  stencils/
    data-world/      ← ICM + Postgres blackboard + Hearsay-II
      agent.md           the LLM orientation file (entry point)
      disciplines/       blank discipline + _template to copy
      brain/             schema, schema map, access contract
      lib/               blackboard read/write, gate pattern, stage runtime, tools
                         watch.py + dispatch.py — the scheduler (activation layer)
                         workflow_runtime.py — multi-discipline workflow runner
      migrations/        001_init.sql first, then 002_activation.sql for the scheduler
      workflows/         runnable multi-discipline workflows, including a business-ops example
      workspaces/        per-entity workspace pattern
      config.yaml        world path + db connection
      data_packet_spec.md what flows between stages

    dev-world/       ← ICM + filesystem blackboard + 5-phase loop
      CLAUDE.md          the LLM orientation file (entry point)
      CONTEXT.md         the discipline router
      INDEX.md           whole-domain map in one read
      disciplines/       debug / feature / refactor / review / test + _template
      workflows/
        ringer/          the gauntlet every change must pass
      lib/               run_tests.py / who_calls.py / commit_gate.py
```

---

## License

MIT. Build your World.
