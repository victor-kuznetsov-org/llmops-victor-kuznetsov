import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from pkgscout.agent import run_turn
from pkgscout.memory import ChatMemory
from pkgscout.tools import ToolInfo, version_spec


def _resp(content=None, calls=None):
    message = SimpleNamespace(content=content, tool_calls=calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_run_turn_calls_tool_then_answers() -> None:
    fn = SimpleNamespace(name="latest_version", arguments=json.dumps({"name": "httpx"}))
    call = SimpleNamespace(id="c1", function=fn)
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp(calls=[call]), _resp("0.28")]
    tool = ToolInfo(name="latest_version", spec=version_spec(), exec_fn=lambda name: f"{name} 0.28")
    new = run_turn(client, "m", [tool], [{"role": "user", "content": "q"}])
    assert [m["role"] for m in new] == ["assistant", "tool", "assistant"]
    assert new[1]["content"] == "httpx 0.28"


def test_memory_save_load() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = [({"role": "user"},)]
    mem = ChatMemory(conn)
    mem.save("s", [{"role": "user", "content": "x"}])
    assert mem.load("s") == [{"role": "user"}]
