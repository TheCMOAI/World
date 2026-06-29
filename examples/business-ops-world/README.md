# Business Ops World Example

This example shows the public stencil pattern with a neutral operations domain.

It models a small service-business operating loop:

1. `ops-intake` reads an incoming customer or job request and writes an
   `intake_summary`.
2. `ops-quote` reads that intake artifact and writes a `quote_plan`.
3. `ops-schedule` reads the quote artifact and writes a `schedule_plan`.
4. `ops-followup` reads the schedule artifact and writes a `followup_plan`.

The handoff surface is Postgres, not direct imports between disciplines. Run the
example from `stencils/data-world`:

```bash
python lib/workflow_runtime.py --workflow service-business-ops --entity-id <uuid> --json
```
