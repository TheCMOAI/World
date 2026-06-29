# WORLD-SPEC — Rivertown Plumbing (worked example)

This is what a finished `WORLD-SPEC.md` looks like coming out of `DISCOVER.md`.
It's a real-shaped example for a small residential plumbing business — read it to
see the destination, then run your own interview. Yours will look different; the
shape is the point.

---

## The business
Rivertown Plumbing is a 3-tech residential plumbing company. Most work starts as a
phone call or a site visit, turns into a written quote, and — if the customer says
yes — gets scheduled, done, invoiced, and (ideally) reviewed. The owner quotes
fast but loses money on quotes that go cold and rarely gets around to asking happy
customers for reviews.

## Stencil
data-world

## Entity
**job** — a single piece of work from first call → quote → scheduled → completed →
paid → reviewed. (Rename `entity` → `job` throughout the World.)

## First discipline  [BUILD THIS ONE]
**quote-followup** — chase quotes that have gone quiet, so fewer deals die from
silence.
- Produces: a friendly, specific follow-up message sent to the customer, plus a
  logged record of what was sent and when.
- How it works today → stages:
  - read:    pull every job where a quote was sent, the customer hasn't replied,
             and it's been 2+ days; with that customer's history and the quote amount.
  - plan:    decide which jobs are worth a nudge, what each message should say
             (reference the actual work and price), and how to send it (text first,
             email fallback).
  - execute: send the message, then write the outcome back to the job's history
             and update "last contact."
- Gates: sending the message to the customer needs the owner's okay for now
  (it's going to a real person). Loosen to automatic once he trusts the drafts.
- Wakes itself when: a job's quote has been sent, has no reply, and was sent more
  than 2 days ago. At most once every 48 hours per job.

## Remember per job
- quote_amount — what was quoted, to reference in the follow-up
- last_contact — when the customer was last touched, drives the wake condition
- channel — text or email, whichever the customer answered on
- followup_count — how many nudges have gone out, so we stop after two

## Later disciplines (noted, not built yet)
- review-request — after a job is marked paid, ask the customer for a Google review
- parts-reorder — when a common part drops below a threshold, draft a reorder
- scheduling — turn an accepted quote into a booked slot for the right tech

## Build path
- [ ] Build it myself — run BUILD.md with this spec
- [ ] Have it built for me — <booking link>

---

### How this maps to the World (for the curious — buyers never need this)

| Spec line | What it becomes |
|-----------|-----------------|
| entity = "job" | the `entities` table, renamed; domain fields in `metadata` |
| quote-followup | one discipline, `disciplines/quote-followup/` |
| read / plan / execute | `stages/01_read`, `02_plan`, `03_execute` |
| gate on sending | a `gate` before the execute stage's send action |
| "wakes itself when…" | an `activation: mode: condition` block in `binding.yaml`, run by `lib/watch.py` |
| remember per job | columns / `learnings` the read stage pulls |
