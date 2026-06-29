# Contributing

Three ways to contribute:

---

## 1. Submit a World you built

Add it to `WORLDS.md`. One row, one PR. Title: `worlds: add <your-world-name>`.

---

## 2. Improve the stencils

The stencils live in `stencils/`. Welcome:
- Clearer CONTEXT.md documentation in any discipline
- Better example discipline implementations
- Additional worked examples (matching the `example-notes/` style — real Python, real DB reads/writes)
- Fixes to `world_doctor.py` or the lib layer
- Improvements to `harness.py` — better error messages, multi-turn history, streaming output

Run `world_doctor.py` before submitting any data-world change:

```bash
cd stencils/data-world
python lib/world_doctor.py
```

Run the dev-world tests before submitting any dev-world change:

```bash
cd stencils/dev-world
python lib/run_tests.py
```

---

## 3. Open an issue

If you hit a wall that `BUILD.md` didn't warn you about, open an issue.
The shortcomings list exists to be complete — a missing warning is a bug.

---

## What we are not looking for

- New architectures that compete with or replace ICM / blackboard / Hearsay-II
- Frontend code or hosted services
- LLM-vendor-specific code in the core stencil (`harness.py` is the only vendor file and it stays optional and swappable)
- New top-level folders that don't fit inside `stencils/`
