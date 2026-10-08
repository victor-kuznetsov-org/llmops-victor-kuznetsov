"""A tool-calling agent loop of our own over pkgscout's tools."""

import json
from typing import Any

from pkgscout.tools import ToolInfo

SYSTEM_PROMPT = (
    "You answer questions about popular Python packages. Use search_chunks for how a package "
    "is used and latest_version for its latest version. Be brief."
)


def run_turn(
    client: Any,
    endpoint: str,
    tools: list[ToolInfo],
    messages: list[dict],
    max_steps: int = 5,
) -> list[dict]:
    """Append to `messages` until the model answers; return the new messages of this turn."""
    registry = {t.name: t for t in tools}
    start = len(messages)
    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=endpoint, messages=messages, tools=[t.spec for t in tools], max_tokens=800
        )
        msg = resp.choices[0].message
        entry: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments},
                }
                for c in msg.tool_calls
            ]
        messages.append(entry)
        if not msg.tool_calls:
            break
        for c in msg.tool_calls:
            try:
                out = registry[c.function.name].exec_fn(**json.loads(c.function.arguments or "{}"))
            except Exception as e:  # noqa: BLE001
                out = f"tool error: {e}"
            messages.append({"role": "tool", "tool_call_id": c.id, "content": str(out)})
    return messages[start:]
