# <Discipline> / 03_build

**Job:** Execute the plan. Smallest change that does the job.

## Inputs
- Plan from 02_plan

## Process
1. Make the change — match surrounding style, naming, comment density
2. Check every caller in the blast radius — nothing broken
3. Write a test if the change affects observable behavior
4. Run `python lib/run_tests.py --select <path>` to confirm

## Outputs
- Edited file(s)
- New test if applicable
- Targeted tests passing

## Gate
None here — `04_verify` is the gate.
