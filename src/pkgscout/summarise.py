"""Summarise a package's PyPI description with the course's chat model service."""

from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "project_config.yml"


def get_client() -> Any:
    """OpenAI client of the course's AI Gateway (profile from DATABRICKS_CONFIG_PROFILE)."""
    from databricks_openai import DatabricksOpenAI

    return DatabricksOpenAI(use_ai_gateway=True)


def llm_endpoint(env: str = "dev") -> str:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)[env]["llm_endpoint"]


def summarise(client: Any, endpoint: str, name: str, description: str) -> tuple[str, dict]:
    """Summarise one package's description in three lines; return (text, token usage)."""
    response = client.chat.completions.create(
        model=endpoint,
        messages=[
            {"role": "system", "content": "You summarise Python packages in exactly three lines."},
            {"role": "user", "content": f"Package: {name}\n\n{description[:4000]}"},
        ],
        max_tokens=400,
    )
    usage = response.usage
    return response.choices[0].message.content, {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }
