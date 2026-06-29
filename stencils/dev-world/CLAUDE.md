# DEV World — Layer 0 (Identity)

> You are inside a **Dev World** — a development operating domain for a codebase.
> This file answers one question: **"Where am I?"** It is always loaded. It does
> not do work — it tells you where work lives and the rules that apply everywhere.

## Where you are

A development task has entered this World — a bug to fix, a feature to add, a
refactor, a review. Your job is to route it to the right discipline, run it through
stages, and **leave the test suite no redder than you found it**.

If you are about to edit code before finishing IDENTIFY and PLAN, stop.

## The folder map

```
dev-world/
├── CLAUDE.md      ← you are here (Layer 0 — "where am I")
├── CONTEXT.md     ← the router ("where do I go next")
├── INDEX.md       ← whole-domain map in one read
├── disciplines/   ← single-capability units
│   ├── debug/     reproduce → isolate → fix → verify
│   ├── feature/   plan → build → test → verify
│   ├── refactor/  map → cover → refactor → verify
│   ├── review/    inspect → assess → report
│   └── test/      run → triage → report
├── workflows/
│   └── ringer/    ← the gauntlet every change must pass
└── lib/           ← real tools. Deterministic, no AI. Shell these:
    ├── run_tests.py    catch-net — runs the suite, survives broken collectors
    ├── who_calls.py    blast radius — who references a symbol (live grep)
    └── commit_gate.py  gate — blocks changes that newly break tests
```

## The blackboard

This World has no Postgres database. The blackboard is the **codebase itself** —
the files, the git history, and the test results. The LLM reads state by reading
files and running `lib/` tools. It writes state by editing files and committing.

## The universal law — the 5-phase loop

Every non-trivial change runs the same five phases. This is the spine:

```
1. IDENTIFY  — what is it, where does it live, what reads it
2. PLAN      — who_calls.py before touching load-bearing code
3. BUILD     — smallest change that does the job
4. TEST      — run_tests.py on the affected scope
5. VERIFY    — commit_gate.py — no new red
```

Phases 2 and 5 are non-negotiable for anything touching shared state.

## Rules

1. **Never commit red you caused.** `commit_gate.py` is the one rule that stops
   bug-printing. Pre-existing red is tolerated via a baseline; new red is not.

2. **Read the blast radius before editing load-bearing code.** Run
   `python lib/who_calls.py <symbol>` before changing a function's signature
   or behavior. A 2-second check beats an unseen caller broken for hours.

3. **Smallest change that works.** Match surrounding code style, naming, and
   comment density. Wide diffs are where bugs hide.

4. **A bug gets a test.** Fix a bug → add a test that failed before and passes
   after. The same bug never ships twice.

5. **One stage, one job.** A stage reads defined inputs, transforms, writes defined
   outputs. It does not also do the next stage's work.

6. **Gates stop you.** Destructive git (force-push, reset --hard), a red gate,
   ambiguous targets → stop and surface it. Don't push past a gate on a guess.

7. **Tools are real, not advisory.** `lib/` scripts actually run. Use them; don't
   narrate that you "would" check the blast radius — run `who_calls.py`.

## Naming

| Thing            | Pattern                      | Example                   |
|------------------|------------------------------|---------------------------|
| Stage folder     | `NN_verb` (NN = order)       | `03_fix/`                 |
| Stage contract   | `CONTEXT.md`                 | `stages/03_fix/CONTEXT.md`|
| Discipline       | kebab-case folder            | `debug/`, `feature/`      |
| Working artifact | `[slug]-[status].md`         | `bug-42-draft.md`         |
