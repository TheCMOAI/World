#!/usr/bin/env python3
"""
watch.py - the World scheduler (the third leg of Hearsay-II).

The blackboard holds state. The disciplines do the work. This watches the
blackboard and decides WHEN a discipline should wake up - without an operator
typing a request. It is what turns a reactive World into an autonomous one.

Each discipline declares its own activation condition in binding.yaml. There is
no central broker routing requests through a flowchart - the watcher just
evaluates each discipline's own condition and lets it self-select.

One pass:
  1. Read every discipline's binding.yaml -> activation block.
  2. For disciplines with `mode: condition`, run the activation query (read-only).
  3. Each returned row is a candidate entity. Skip candidates still inside their
     cooldown window (already proposed recently).
  4. Write an `activations` row (status=proposed) for each fresh candidate.

It NEVER mutates an entity and never runs a stage. It only proposes work.
lib/dispatch.py turns proposals into opened stages.

Usage:
    python lib/watch.py --once                # one pass - run this from cron/launchd
    python lib/watch.py --loop --interval 60  # poll every 60s (dev convenience)
    python lib/watch.py --once --dry-run      # show what would fire, write nothing

The activation query is authored by the World builder (like a migration) and run
by this watcher - infrastructure, not the operating LLM. The tool fence still
binds the LLM; this does not widen it.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORLD_ROOT = Path(__file__).resolve().parent.parent
DISCIPLINES_ROOT = WORLD_ROOT / "disciplines"

sys.path.insert(0, str(WORLD_ROOT / "lib"))
from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# -- cooldown parsing --------------------------------------------------------

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_cooldown(value) -> timedelta:
    """'30m' / '24h' / '7d' -> timedelta. Empty -> no cooldown."""
    if not value:
        return timedelta(0)
    m = re.fullmatch(r"\s*(\d+)\s*([smhd])\s*", str(value).lower())
    if not m:
        raise ValueError(f"bad cooldown {value!r} (use forms like 30m, 24h, 7d)")
    return timedelta(seconds=int(m.group(1)) * _UNITS[m.group(2)])


# -- query safety ------------------------------------------------------------

def validate_query(query: str) -> str:
    """Activation queries must be a single read-only SELECT. Builder-authored,
    but we keep the watcher honest: no DML, no multiple statements."""
    q = query.strip().rstrip(";").strip()
    if ";" in q:
        raise ValueError("activation query must be a single statement (no ';')")
    if not re.match(r"(?is)^\s*(select|with)\b", q):
        raise ValueError("activation query must be a SELECT")
    bad = re.search(r"(?is)\b(insert|update|delete|drop|alter|truncate|create|grant)\b", q)
    if bad:
        raise ValueError(f"activation query may not contain '{bad.group(1)}'")
    return q


def _select(query: str) -> list:
    """Run a read-only SELECT and return rows as dicts. Infra path - parallel to
    world_doctor, which also connects directly. Not exposed to the LLM."""
    import psycopg2
    import psycopg2.extras

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    with psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [dict(r) for r in cur.fetchall()]


# -- binding discovery -------------------------------------------------------

def _disciplines() -> list:
    return [
        d for d in sorted(DISCIPLINES_ROOT.iterdir())
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    ]


def _activation(discipline_dir: Path) -> dict | None:
    binding = discipline_dir / "binding.yaml"
    if not binding.exists():
        return None
    data = yaml.safe_load(binding.read_text()) or {}
    return data.get("activation")


def _within_cooldown(trigger_key: str, cooldown: timedelta) -> bool:
    if cooldown.total_seconds() <= 0:
        return False
    recent = blackboard_read(
        "activations",
        filter={"trigger_key": trigger_key},
        order_by="created_at DESC",
        limit=1,
    )
    if not recent:
        return False
    if isinstance(recent, list):
        recent = recent[0]
    created = recent.get("created_at")
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created) < cooldown


# -- the pass ---------------------------------------------------------------

def run_pass(dry_run: bool = False) -> list:
    proposed = []
    for d in _disciplines():
        act = _activation(d)
        if not act or act.get("mode") != "condition":
            continue

        query = act.get("query")
        if not query:
            print(f"  !  {d.name}: mode is 'condition' but no query - skipping")
            continue
        try:
            q = validate_query(query)
            cooldown = parse_cooldown(act.get("cooldown"))
        except ValueError as e:
            print(f"  x  {d.name}: {e}")
            continue

        risk = act.get("risk", "low")
        try:
            candidates = _select(q)
        except Exception as e:
            print(f"  x  {d.name}: query failed: {e}")
            continue

        for row in candidates:
            entity_id = row.get("entity_id") or row.get("id")
            if not entity_id:
                print(f"  x  {d.name}: query row has no entity_id column - {row}")
                continue
            trigger_key = f"{d.name}:{entity_id}"
            if _within_cooldown(trigger_key, cooldown):
                continue
            reason = row.get("reason") or act.get("reason") or f"{d.name} condition met"

            if dry_run:
                print(f"  .  would propose {trigger_key}  ({reason})")
                proposed.append(trigger_key)
                continue

            blackboard_write("activations", {
                "discipline": d.name,
                "entity_id": str(entity_id),
                "trigger_key": trigger_key,
                "reason": reason,
                "risk": risk,
                "status": "proposed",
                "detail": json.loads(json.dumps(row, default=str)),
            })
            print(f"  +  proposed {trigger_key}  ({reason})")
            proposed.append(trigger_key)

    if not proposed:
        print("  (no activations this pass)")
    return proposed


def main():
    ap = argparse.ArgumentParser(description="World scheduler - propose discipline activations")
    ap.add_argument("--once", action="store_true", help="run a single pass (default)")
    ap.add_argument("--loop", action="store_true", help="poll continuously")
    ap.add_argument("--interval", type=int, default=60, help="seconds between passes in --loop mode")
    ap.add_argument("--dry-run", action="store_true", help="show what would fire, write nothing")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("Error: DATABASE_URL not set.")
        sys.exit(1)

    if args.loop:
        print(f"watch: looping every {args.interval}s (Ctrl-C to stop)")
        while True:
            print(f"\n-- watch pass @ {datetime.now(timezone.utc).isoformat()} --")
            run_pass(args.dry_run)
            time.sleep(args.interval)
    else:
        run_pass(args.dry_run)


if __name__ == "__main__":
    main()
