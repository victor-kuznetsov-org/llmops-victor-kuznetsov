"""Two tools of pkgscout in the course's tool specification format (spec + exec_fn)."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from pkgscout.vectors import embed, to_pg


class ToolInfo(BaseModel):
    name: str
    spec: dict
    exec_fn: Callable


def search_spec() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "search_chunks",
            "description": "Search the PyPI page chunks of popular Python packages by meaning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to look for."},
                    "k": {"type": "integer", "description": "Number of chunks (default 3)."},
                },
                "required": ["query"],
            },
        },
    }


def version_spec() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "latest_version",
            "description": "Latest released version of a package, from the pypi_packages table.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Package name."}},
                "required": ["name"],
            },
        },
    }


def make_search_tool(conn: Any, client: Any) -> ToolInfo:
    def exec_fn(query: str, k: int = 3) -> str:
        qv = to_pg(embed([query], client)[0])
        hits = conn.execute(
            "SELECT name, heading, left(text, 400) FROM chunk_vectors "
            "ORDER BY vector <=> %s::vector LIMIT %s",
            (qv, int(k)),
        ).fetchall()
        return "\n\n".join(f"[{n} / {h}] {t}" for n, h, t in hits) or "no result"

    return ToolInfo(name="search_chunks", spec=search_spec(), exec_fn=exec_fn)


def make_version_tool(spark: Any, table: str) -> ToolInfo:
    def exec_fn(name: str) -> str:
        rows = spark.sql(
            f"SELECT name, version, release_date FROM {table} WHERE lower(name) = lower(:n)",
            args={"n": name},
        ).collect()
        if not rows:
            return f"no package named {name}"
        r = rows[0]
        return f"{r.name} latest version {r.version} (released {r.release_date})"

    return ToolInfo(name="latest_version", spec=version_spec(), exec_fn=exec_fn)
