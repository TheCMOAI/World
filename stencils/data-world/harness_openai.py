#!/usr/bin/env python3
"""
harness_openai.py - same harness as harness.py, wired to OpenAI instead of Anthropic.

Requires: pip install openai
Set: OPENAI_API_KEY and DATABASE_URL

Usage:
  python harness_openai.py "your first message"
  python harness_openai.py              # interactive REPL
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from harness_core import (
    call_tool_json,
    load_system_prompt,
    open_workspace,
    openai_tools,
    resolve_gate,
    user_message_with_context,
)

WORLD_ROOT = Path(__file__).parent


def run(
    user_message: str,
    model: str | None = None,
    *,
    messages: list | None = None,
    workspace_id: str | None = None,
    return_state: bool = False,
) -> str | tuple[str, list, str]:
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
    workspace_id = workspace_id or open_workspace(name="openai harness session")
    import openai

    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = list(messages or [{"role": "system", "content": load_system_prompt(WORLD_ROOT)}])
    messages.append({"role": "user", "content": user_message_with_context(user_message, workspace_id)})

    for _ in range(20):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools(),
            tool_choice="auto",
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                print(f"  [tool] {tc.function.name}({json.dumps(args)[:120]})", file=sys.stderr)
                result = call_tool_json(tc.function.name, args, workspace_id=workspace_id)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
            continue

        reply = msg.content or ""
        return (reply, messages, workspace_id) if return_state else reply

    reply = "[stopped after tool limit]"
    return (reply, messages, workspace_id) if return_state else reply


def repl():
    workspace_id = open_workspace(name="openai harness repl")
    messages = None
    print(f"World harness (OpenAI) - workspace {workspace_id}. Type your message, Ctrl+C to exit.\n")
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

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        sys.exit(1)
    if not os.environ.get("DATABASE_URL"):
        print("Error: DATABASE_URL not set.")
        sys.exit(1)

    if len(sys.argv) >= 2:
        print(run(" ".join(sys.argv[1:])))
    else:
        repl()
