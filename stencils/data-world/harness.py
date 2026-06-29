#!/usr/bin/env python3
"""
harness.py - the thin bridge between the operator and the World.

Drop this into your data-world root. Set DATABASE_URL and ANTHROPIC_API_KEY.
Run: python harness.py "your first message"

The harness reads agent.md as the system prompt, exposes the 4 tool verbs to
the model, and runs the conversation loop until the model produces a final reply.
Tool calls dispatch to lib/tools.py - the same functions your stage scripts use.

This is intentionally minimal. Extend it: add a web UI, a Slack bot, a cron loop.
The loop and the tool dispatch are the parts worth keeping.
"""

import json
import os
import sys
from pathlib import Path

# --- path setup: lib/ must be on sys.path for tools.py imports to resolve ---
WORLD_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORLD_ROOT / "lib"))

from harness_core import (
    anthropic_tools,
    call_tool_json,
    load_system_prompt,
    open_workspace,
    resolve_gate,
    user_message_with_context,
)


# --- conversation loop ---
def _content_blocks(blocks):
    out = []
    for block in blocks:
        if hasattr(block, "model_dump"):
            out.append(block.model_dump())
        elif hasattr(block, "to_dict"):
            out.append(block.to_dict())
        else:
            out.append(block)
    return out


def run(
    user_message: str,
    model: str | None = None,
    *,
    messages: list | None = None,
    workspace_id: str | None = None,
    return_state: bool = False,
) -> str | tuple[str, list, str]:
    model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    workspace_id = workspace_id or open_workspace(name="anthropic harness session")
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = list(messages or [])
    messages.append({"role": "user", "content": user_message_with_context(user_message, workspace_id)})

    for _ in range(20):
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=load_system_prompt(WORLD_ROOT),
            tools=anthropic_tools(),
            messages=messages,
        )

        messages.append({"role": "assistant", "content": _content_blocks(response.content)})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return (block.text, messages, workspace_id) if return_state else block.text
            return ("", messages, workspace_id) if return_state else ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name}({json.dumps(block.input, default=str)[:120]})", file=sys.stderr)
                    result = call_tool_json(block.name, block.input, workspace_id=workspace_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    reply = "[stopped after tool limit]"
    return (reply, messages, workspace_id) if return_state else reply


# --- multi-turn loop ---
def repl():
    workspace_id = open_workspace(name="anthropic harness repl")
    messages = []
    print(f"World harness - workspace {workspace_id}. Type your message, Ctrl+C to exit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        if not user_input:
            continue
        reply, messages, workspace_id = run(
            user_input,
            messages=messages,
            workspace_id=workspace_id,
            return_state=True,
        )
        print(f"\nWorld: {reply}\n")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--resolve-gate":
        if not os.environ.get("DATABASE_URL"):
            print("Error: DATABASE_URL not set.")
            sys.exit(1)
        print(json.dumps(resolve_gate(sys.argv[2], approved=True, answer="approved"), indent=2, default=str))
        raise SystemExit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set.")
        sys.exit(1)

    if len(sys.argv) >= 2:
        # single message mode
        user_message = " ".join(sys.argv[1:])
        reply = run(user_message)
        print(reply)
    else:
        # interactive REPL
        repl()
