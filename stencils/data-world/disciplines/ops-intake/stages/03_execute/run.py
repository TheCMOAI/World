import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.script_base import print_json, standard_args
from business_example import run_execute


def run(entity_id: str, workspace_id: str) -> dict:
    return run_execute("ops-intake", entity_id, workspace_id)


if __name__ == "__main__":
    args = standard_args("ops-intake / 03_execute").parse_args()
    print_json(run(args.entity_id, args.workspace_id), args.json_only)

