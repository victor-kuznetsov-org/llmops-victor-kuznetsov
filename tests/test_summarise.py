from types import SimpleNamespace
from unittest.mock import MagicMock

from pkgscout.summarise import summarise


def test_summarise_returns_text_and_usage() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="a\nb\nc"))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    text, usage = summarise(client, "some-endpoint", "httpx", "A HTTP client.")

    assert text == "a\nb\nc"
    assert usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    assert client.chat.completions.create.call_args.kwargs["model"] == "some-endpoint"
