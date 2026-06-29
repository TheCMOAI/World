import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.script_base import print_json, standard_args
from business_example import run_plan


def run(entity_id: str, workspace_id: str, objective: str = "") -> dict:
    return run_plan("ops-followup", entity_id, workspace_id, objective)


if __name__ == "__main__":
    parser = standard_args("ops-followup / 02_plan")
    parser.add_argument("--objective", default="")
    args = parser.parse_args()
    print_json(run(args.entity_id, args.workspace_id, args.objective), args.json_only)

