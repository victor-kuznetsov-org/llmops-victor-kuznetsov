"""pgvector on the cohort's Lakebase instance: connect, embed, search."""

import urllib.parse
from uuid import uuid4

import psycopg
from databricks.sdk import WorkspaceClient

EMBED_ENDPOINT = "course_ops.gateway.embed"
DIM = 1024


def connect(profile: str, instance: str, database: str) -> psycopg.Connection:
    """Connect as the profile's principal with a short-lived Lakebase token."""
    w = WorkspaceClient(profile=profile)
    host = w.database.get_database_instance(instance).read_write_dns
    token = w.database.generate_database_credential(
        request_id=str(uuid4()), instance_names=[instance]
    ).token
    user = w.current_user.me().user_name
    return psycopg.connect(
        host=host,
        port=5432,
        dbname=database,
        user=urllib.parse.unquote_plus(user),
        password=token,
        sslmode="require",
        autocommit=True,
    )


def embed(texts: list[str], client, batch: int = 16) -> list[list[float]]:  # noqa: ANN001
    """Embed texts with the course's embedding service (truncated to 2000 characters)."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        resp = client.embeddings.create(
            model=EMBED_ENDPOINT, input=[t[:2000] for t in texts[i : i + batch]]
        )
        out += [d.embedding for d in resp.data]
    return out


def to_pg(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
