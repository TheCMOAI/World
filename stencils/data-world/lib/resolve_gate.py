#!/usr/bin/env python3
"""
resolve_gate.py - CLI to inspect and resolve open gates.

Usage:
  python lib/resolve_gate.py list              # show all open gates
  python lib/resolve_gate.py resolve <gate_id> # approve a gate
  python lib/resolve_gate.py reject <gate_id>  # reject a gate (blocks the action)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write


def list_gates():
    gates = blackboard_read("gates", filter={"status": "open"}, order_by="created_at ASC")
    if not gates:
        print("No open gates.")
        return
    print(f"{len(gates)} open gate(s):\n")
    for g in gates:
        print(f"  ID:         {g['id']}")
        print(f"  Question:   {g['question']}")
        print(f"  Risk:       {g.get('risk_level', 'medium')}")
        print(f"  Created:    {g.get('created_at', '')}")
        resume = g.get("resume_action_json") or "{}"
        if resume and resume != "{}":
            print(f"  On resolve: {resume}")
        print()


def resolve_gate(gate_id: str):
    result = blackboard_write(
        "gates",
        {"status": "resolved"},
        where={"id": gate_id, "status": "open"},
        returning="*"
    )
    if not result:
        print(f"Gate {gate_id} not found or already resolved.")
        sys.exit(1)
    print(f"Gate {gate_id} resolved. The pending action may now proceed.")


def reject_gate(gate_id: str):
    result = blackboard_write(
        "gates",
        {"status": "rejected"},
        where={"id": gate_id, "status": "open"},
        returning="*"
    )
    if not result:
        print(f"Gate {gate_id} not found or already closed.")
        sys.exit(1)
    print(f"Gate {gate_id} rejected. The pending action is blocked.")


def main():
    if not os.environ.get("DATABASE_URL"):
        print("Error: DATABASE_URL not set.")
        sys.exit(1)

    if len(sys.argv) < 2 or sys.argv[1] == "list":
        list_gates()
    elif sys.argv[1] == "resolve" and len(sys.argv) >= 3:
        resolve_gate(sys.argv[2])
    elif sys.argv[1] == "reject" and len(sys.argv) >= 3:
        reject_gate(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
