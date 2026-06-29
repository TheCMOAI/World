# The Activation Model — how a World wakes itself

Hearsay-II had three parts: the **blackboard** (shared state), the **knowledge
sources** (independent experts), and the **scheduler** (the control component
that decides which knowledge source acts next). This stencil gave you the first
two from day one. The blackboard is Postgres; the disciplines are your knowledge
sources. This file is the third: the scheduler.

Without it, a World is **reactive** — a discipline only runs when an operator
types a request. With it, a World is **autonomous** — a discipline wakes itself
when the blackboard meets its condition. That is the difference between "a tool
you drive" and "an operator that runs the business while you sleep."

There is still no central broker. Each discipline declares its *own* activation
condition. The watcher just evaluates them — disciplines self-select, exactly as
Hearsay-II intended.

---

## The loop: sense → propose → dispatch

```
            ┌─────────────────────────────────────────────┐
            │              blackboard (Postgres)           │
            └─────────────────────────────────────────────┘
                 ▲                  │                  ▲
        write    │           read   │   read           │  write
     activations │                  ▼                  │  packets / outcomes
            ┌─────────┐        ┌──────────┐       ┌──────────────────┐
            │ watch.py│ ─────▶ │dispatch.py│ ────▶ │ discipline stages │
            │ (sense) │ propose│  (open)   │ open  │ read→plan→execute │
            └─────────┘        └──────────┘       └──────────────────┘
```
1. **Sense** — `lib/watch.py` reads each discipline's `activation` block from
   `binding.yaml`. For disciplines in `mode: condition`, it runs the query
   against the blackboard. Every returned row is a candidate entity.

2. **Propose** — for each fresh candidate (not inside its cooldown window) it
   writes a row to `activations` with `status = proposed`. The proposal lives on
   the blackboard, so it is observable and auditable — you can always answer
   "what does the World want to do right now, and why."

3. **Dispatch** — `lib/dispatch.py` reads proposed activations and opens the
   discipline's **entry (read) stage** for each. It writes back
   `status = dispatched` and the workspace it opened.

The operating LLM (or a higher-tier loop) then picks up the open workspace and
runs plan → execute under the normal rules and gates.

---

## The safety boundary (read this twice)

**The scheduler senses and opens. It never plans and never mutates.**

`dispatch.py` runs only the `01_read` stage. It does not call plan or execute.
Mutations stay behind the read → plan → execute flow and its gates, where a model
(and, for anything irreversible, a human) is in the loop. This is deliberate: an
autonomous loop that can `03_execute` on its own is exactly how unattended agents
cause damage.

Two further guards:

- **Cooldown.** `cooldown: 24h` means the same `discipline:entity` pair will not
  be re-proposed within 24 hours, even if the condition stays true. Without this,
  a standing condition floods the table every pass.
- **Risk gate.** `risk: high` makes the dispatcher open a **gate** instead of a
  stage. No work begins until a human resolves it (`lib/resolve_gate.py`).

---

## Declaring a condition

In a discipline's `binding.yaml`:

```yaml
activation:
  mode: condition          # manual (default) | condition
  query: |
    SELECT id AS entity_id
    FROM entities
    WHERE status = 'active'
      AND (metadata->>'last_contact')::timestamptz < now() - interval '7 days'
  entry_stage: 01_read     # which stage dispatch opens (default 01_read)
  cooldown: 24h            # don't re-propose the same entity within this window
  risk: low                # low | medium | high — high opens a gate first
```

Rules for the query:

- It must be a **single read-only SELECT** (the watcher rejects DML and multiple
  statements). It is authored by you, the builder, like a migration — not by the
  operating LLM. The tool fence is unchanged.
- It must return a column named **`entity_id`** (alias `id AS entity_id` if
  needed). Each row is one candidate.
- It may return an optional **`reason`** column — plain text stored on the
  activation so the proposal explains itself.

`mode: manual` (the default) keeps a discipline reactive — it runs only when
called. Leave new disciplines manual until you trust their condition.

---

## Worked example — customer follow-up

> Wake the `customer-followup` discipline for any active request we have not
> contacted in 7 days, at most once a day per request.

```yaml
# disciplines/customer-followup/binding.yaml
activation:
  mode: condition
  query: |
    SELECT id AS entity_id,
           'no contact in ' || date_part('day', now() - (metadata->>'last_contact')::timestamptz)
             || ' days' AS reason
    FROM entities
    WHERE status = 'active'
      AND (metadata->>'last_contact')::timestamptz < now() - interval '7 days'
  entry_stage: 01_read
  cooldown: 24h
  risk: low
```

Then:

```bash
python lib/watch.py --once --dry-run   # see which requests would fire
python lib/watch.py --once             # propose them
python lib/dispatch.py --once          # open 01_read for each
```

---

## Running the scheduler

`watch.py --once` and `dispatch.py --once` are designed to be run on a timer. Do
not rely on `--loop` in production — a real scheduler should be cron or launchd
so it survives reboots and you get logs.

**cron (Linux):**

```cron
*/5 * * * *  cd /path/to/world && DATABASE_URL=postgresql://... python lib/watch.py --once    >> watch.log 2>&1
*/5 * * * *  cd /path/to/world && DATABASE_URL=postgresql://... python lib/dispatch.py --once >> dispatch.log 2>&1
```

**launchd (macOS):** a `StartInterval` plist calling the same two commands.

`--loop --interval 60` exists for local development only.

---

## What this still does not do (be honest about it)

- **No full auto-execution.** Dispatch opens the read stage; it does not drive
  plan/execute. If you want low-risk disciplines to run end-to-end unattended,
  you build that loop on top — and you own the consequences of removing the human
  from the loop. Start by auto-running only `reversible: true` actions.
- **No failed-activation retry.** A dispatched activation that errors in its read
  stage is recorded, not retried. Build retry/backoff when you need it.
- **No priority ordering.** Proposals dispatch oldest-first. If two disciplines
  contend for the same entity, add a priority column and order by it.
- **Cooldown is time-based, not outcome-aware.** It prevents re-proposing too
  soon; it does not know whether the last run succeeded. Pair it with a condition
  that excludes already-handled entities (e.g. check `last_contact` was updated).
```
