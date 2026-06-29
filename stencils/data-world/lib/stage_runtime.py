"""
Stage Runtime - dispatches run_stage calls to the right discipline and stage.

This is the harness. The LLM calls run_stage via the tool interface and this
module finds and executes the right stage script.

Usage (as a tool backend):
    stage_runtime.dispatch("customer-research", "01_read", {"entity_id": "...", "workspace_id": "..."})

Usage (from CLI):
    python stage_runtime.py --discipline customer-research --stage 01_read --args '{"entity_id": "..."}'
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from contextlib import contextmanager

WORLD_ROOT = Path(__file__).parent.parent
DISCIPLINES_ROOT = WORLD_ROOT / "disciplines"
os.environ.setdefault("WORLD_ROOT", str(WORLD_ROOT))


@contextmanager
def _stage_env(discipline: str, stage_name: str):
    previous = {
        "WORLD_ACTIVE_DISCIPLINE": os.environ.get("WORLD_ACTIVE_DISCIPLINE"),
        "WORLD_ACTIVE_STAGE": os.environ.get("WORLD_ACTIVE_STAGE"),
    }
    os.environ["WORLD_ACTIVE_DISCIPLINE"] = discipline
    os.environ["WORLD_ACTIVE_STAGE"] = stage_name
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _packet_write_env():
    previous = os.environ.get("WORLD_INTERNAL_PACKET_WRITE")
    os.environ["WORLD_INTERNAL_PACKET_WRITE"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("WORLD_INTERNAL_PACKET_WRITE", None)
        else:
            os.environ["WORLD_INTERNAL_PACKET_WRITE"] = previous


def dispatch(discipline: str, stage: str, args: dict) -> dict:
    """
    Find and run the stage script for the given discipline and stage.

    discipline: folder name under disciplines/ (e.g. "customer-research")
    stage:      stage folder name (e.g. "01_read") or just the number ("01")
    args:       dict of arguments passed to the stage's run() function
    """
    discipline_path = DISCIPLINES_ROOT / discipline
    if not discipline_path.exists():
        return {"error": f"Discipline not found: {discipline}", "available": _list_disciplines()}

    # Resolve partial stage names ("01" -> "01_read")
    stage_path = _resolve_stage(discipline_path, stage)
    if not stage_path:
        return {
            "error": f"Stage not found: {stage} in {discipline}",
            "available": _list_stages(discipline_path),
        }

    run_script = stage_path / "run.py"
    if not run_script.exists():
        return {"error": f"No run.py in {stage_path}"}

    # Load and call run()
    spec = importlib.util.spec_from_file_location("stage_run", run_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "run"):
        return {"error": f"run.py in {stage_path} has no run() function"}

    with _stage_env(discipline, stage_path.name):
        result = module.run(**args)

    _persist_stage_packet(discipline, stage_path.name, result)
    return result


def _persist_stage_packet(discipline: str, stage_name: str, result: dict) -> None:
    if not isinstance(result, dict) or result.get("error"):
        return
    workspace_id = result.get("workspace_id")
    entity_id = result.get("entity_id")
    if not workspace_id or not entity_id:
        return

    from _shared.db.write import blackboard_write

    packet = dict(result)
    packet.setdefault("discipline", discipline)
    packet.setdefault("stage", stage_name)
    with _packet_write_env():
        blackboard_write(
            "stage_packets",
            {
                "workspace_id": workspace_id,
                "entity_id": entity_id,
                "discipline": discipline,
                "stage": stage_name,
                "packet": packet,
            },
        )


def _resolve_stage(discipline_path: Path, stage: str) -> Path | None:
    stages_path = discipline_path / "stages"
    if not stages_path.exists():
        return None

    for folder in sorted(stages_path.iterdir()):
        if folder.is_dir():
            if folder.name == stage or folder.name.startswith(stage + "_") or folder.name.startswith(stage):
                return folder

    return None


def _list_disciplines() -> list:
    return [d.name for d in DISCIPLINES_ROOT.iterdir() if d.is_dir() and not d.name.startswith("_")]


def _list_stages(discipline_path: Path) -> list:
    stages_path = discipline_path / "stages"
    if not stages_path.exists():
        return []
    return [s.name for s in sorted(stages_path.iterdir()) if s.is_dir()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="World stage runtime")
    parser.add_argument("--discipline", required=True, help="Discipline folder name")
    parser.add_argument("--stage", required=True, help="Stage folder name or number prefix")
    parser.add_argument("--args", default="{}", help="JSON args passed to run()")
    cli_args = parser.parse_args()

    result = dispatch(cli_args.discipline, cli_args.stage, json.loads(cli_args.args))
    print(json.dumps(result, indent=2, default=str))
