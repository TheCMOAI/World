# <Discipline Name> — Stage Router

**Job:** One sentence. What single capability does this discipline own?

## Stage map

| the task is…          | entry stage    | runs through        |
|-----------------------|----------------|---------------------|
| full run              | `01_identify`  | 01 → 02 → 03 → 04   |
| skip to build         | `03_build`     | 03 → 04             |
| verify only           | `04_verify`    | 04 only             |

## Stages

```
stages/
  01_identify/   understand the target — what it is, where it lives, what reads it
  02_plan/       map consequences, define the approach, check blast radius
  03_build/      execute the smallest change that does the job
  04_verify/     commit_gate passes; no new red
```

## Law

- No code changes in `01_identify` or `02_plan`. Reading only.
- `03_build` ships with a test if the change affects observable behavior.
- `04_verify` is not done until `commit_gate.py` passes.
