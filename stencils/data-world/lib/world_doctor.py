#!/usr/bin/env python3
"""
world_doctor.py - validates that a data-world is set up correctly.

Run this after first setup, after adding a new discipline, or when something
is broken and you don't know why. It checks the environment, the database,
and the world structure and reports exactly what is missing or wrong.

Usage:
    python lib/world_doctor.py
    python lib/world_doctor.py --fix     # attempt to fix auto-fixable issues
    python lib/world_doctor.py --json    # machine-readable output

Exit: 0 if all checks pass, 1 if any check fails.
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

WORLD_ROOT = Path(__file__).parent.parent
DISCIPLINES_ROOT = WORLD_ROOT / "disciplines"

REQUIRED_DISCIPLINE_FILES = ["CONTEXT.md", "binding.yaml"]
REQUIRED_STAGE_FILES = ["CONTEXT.md"]
PLACEHOLDER_STRINGS = ["<Discipline Name>", "<your", "<one sentence", "<describe", "PLACEHOLDER"]

checks_passed = []
checks_failed = []
checks_warned = []


def ok(msg: str):
    checks_passed.append(msg)
    print(f"  OK    {msg}")


def fail(msg: str, fix: str = None):
    checks_failed.append({"msg": msg, "fix": fix})
    print(f"  FAIL  {msg}")
    if fix:
        print(f"        fix: {fix}")


def warn(msg: str):
    checks_warned.append(msg)
    print(f"  WARN  {msg}")


def check_environment():
    print("\n-- Environment --")

    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        ok(f"DATABASE_URL is set")
    else:
        fail(
            "DATABASE_URL is not set",
            "export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname"
        )

    try:
        import psycopg2
        ok("psycopg2 is installed")
    except ImportError:
        fail("psycopg2 is not installed", "pip install psycopg2-binary")


def check_database():
    print("\n-- Database --")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        warn("Skipping database checks - DATABASE_URL not set")
        return

    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        ok("Postgres connection successful")
    except Exception as e:
        fail(f"Cannot connect to Postgres: {e}", "Check DATABASE_URL and ensure Postgres is running")
        return

    # Check core tables exist
    core_tables = [
        "entities",
        "workspaces",
        "workflow_runs",
        "workflow_steps",
        "stage_packets",
        "decisions",
        "learnings",
        "gates",
        "entity_activity_log",
        "entity_notes",
        "business_artifacts",
    ]
    try:
        cur = conn.cursor()
        for table in core_tables:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table,)
            )
            exists = cur.fetchone()[0]
            if exists:
                ok(f"Table '{table}' exists")
            else:
                fail(
                    f"Table '{table}' does not exist",
                    "Run: psql $DATABASE_URL < migrations/001_init.sql"
                )

        # Activation layer (migration 002) - optional. A World still runs
        # reactively without it; it is only needed for the scheduler.
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'activations')"
        )
        if cur.fetchone()[0]:
            ok("Table 'activations' exists (scheduler enabled)")
        else:
            warn("Table 'activations' not found - run migrations/002_activation.sql to enable the scheduler")

        _check_write_surface_tables(cur)

        conn.close()
    except Exception as e:
        fail(f"Could not query tables: {e}")


def check_structure():
    print("\n-- World structure --")

    # Check agent.md
    agent_md = WORLD_ROOT / "agent.md"
    if agent_md.exists():
        content = agent_md.read_text()
        if any(p in content for p in ["Replace this preamble", "Replace everything above"]):
            warn("agent.md still contains placeholder text - fill in your domain identity")
        else:
            ok("agent.md has domain content")
    else:
        fail("agent.md not found", "This is your LLM entry point - required")

    # Check disciplines
    if not DISCIPLINES_ROOT.exists():
        fail("disciplines/ directory not found")
        return

    real_disciplines = [
        d for d in DISCIPLINES_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    ]

    if not real_disciplines:
        warn("No disciplines found (only _template). Copy _template to build your first discipline.")
    else:
        ok(f"{len(real_disciplines)} discipline(s) found: {', '.join(d.name for d in real_disciplines)}")

    for discipline in real_disciplines:
        _check_discipline(discipline)


def _check_discipline(discipline: Path):
    name = discipline.name

    for required_file in REQUIRED_DISCIPLINE_FILES:
        f = discipline / required_file
        if not f.exists():
            fail(f"disciplines/{name}/{required_file} missing")
        else:
            content = f.read_text()
            if any(p in content for p in PLACEHOLDER_STRINGS):
                warn(f"disciplines/{name}/{required_file} still has placeholder text")
            else:
                ok(f"disciplines/{name}/{required_file} OK")

    stages_dir = discipline / "stages"
    if not stages_dir.exists():
        fail(f"disciplines/{name}/stages/ not found")
        return

    stages = sorted([s for s in stages_dir.iterdir() if s.is_dir()])
    if not stages:
        warn(f"disciplines/{name}/stages/ is empty - no stages defined")
    else:
        for stage in stages:
            context = stage / "CONTEXT.md"
            if not context.exists():
                fail(f"disciplines/{name}/stages/{stage.name}/CONTEXT.md missing")
            else:
                content = context.read_text()
                if any(p in content for p in PLACEHOLDER_STRINGS):
                    warn(f"disciplines/{name}/stages/{stage.name}/CONTEXT.md has placeholder text")


def _check_write_surface_tables(cur):
    if not DISCIPLINES_ROOT.exists():
        return
    try:
        import yaml
    except ImportError:
        warn("Skipping write_surface table checks - PyYAML is not installed")
        return

    for discipline in DISCIPLINES_ROOT.iterdir():
        if not discipline.is_dir() or discipline.name.startswith("_") or discipline.name.startswith("."):
            continue
        binding = discipline / "binding.yaml"
        if not binding.exists():
            continue
        data = yaml.safe_load(binding.read_text()) or {}
        for table in data.get("write_surface") or []:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table,),
            )
            if cur.fetchone()[0]:
                ok(f"write_surface table '{table}' exists for {discipline.name}")
            else:
                fail(
                    f"write_surface table '{table}' for {discipline.name} does not exist",
                    "Add it to migrations/001_init.sql or remove it from binding.yaml",
                )


def check_lib():
    print("\n-- Lib --")

    required = ["stage_runtime.py", "workflow_runtime.py", "tools.py", "harness_core.py"]
    for f in required:
        path = WORLD_ROOT / "lib" / f
        if path.exists():
            ok(f"lib/{f} OK")
        else:
            fail(f"lib/{f} missing - required by the harness")

    # Check world_doctor can import the db module
    try:
        sys.path.insert(0, str(WORLD_ROOT / "lib"))
        spec = importlib.util.spec_from_file_location(
            "read", WORLD_ROOT / "lib" / "_shared" / "db" / "read.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            ok("lib/_shared/db/read.py importable")
    except Exception as e:
        warn(f"lib/_shared/db/read.py import check failed: {e}")


def main(fix: bool = False, json_output: bool = False) -> int:
    print(f"World Doctor - checking {WORLD_ROOT}")

    check_environment()
    check_database()
    check_structure()
    check_lib()

    print(f"\n-- Summary --")
    print(f"  {len(checks_passed)} passed | {len(checks_failed)} failed | {len(checks_warned)} warnings")

    if json_output:
        print(json.dumps({
            "passed": checks_passed,
            "failed": checks_failed,
            "warned": checks_warned,
            "ok": len(checks_failed) == 0,
        }, indent=2))

    if checks_failed:
        print(f"\n  World is NOT ready. Fix the {len(checks_failed)} failure(s) above.")
        return 1
    elif checks_warned:
        print(f"\n  World is operational but has {len(checks_warned)} warning(s) to address.")
        return 0
    else:
        print(f"\n  World is healthy.")
        return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="World Doctor - validate world setup")
    ap.add_argument("--fix", action="store_true", help="attempt to fix auto-fixable issues")
    ap.add_argument("--json", action="store_true", dest="json_output", help="machine-readable output")
    args = ap.parse_args()
    sys.exit(main(args.fix, args.json_output))
