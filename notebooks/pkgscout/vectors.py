# Databricks notebook source
from pathlib import Path

import yaml
from databricks.connect import DatabricksSession
from databricks_openai import DatabricksOpenAI

from pkgscout.vectors import DIM, connect, embed, to_pg

PROFILE = "student-victor-kuznetsov"
CONFIG = (
    Path(__file__).resolve().parents[2] / "project_config.yml"
    if "__file__" in globals()
    else Path("project_config.yml")
)
cfg = yaml.safe_load(CONFIG.read_text())["dev"]
if not (cfg.get("lakebase_instance") and cfg.get("lakebase_database")):
    raise SystemExit("lakebase_instance / lakebase_database missing: stopping 2.4")

spark = DatabricksSession.builder.profile(PROFILE).serverless(True).getOrCreate()
rows = spark.table(f"{cfg['catalog']}.{cfg['schema']}.package_chunks").collect()
client = DatabricksOpenAI(use_ai_gateway=True)
vectors = embed([r.text for r in rows], client)
print(len(vectors), "embeddings of", len(vectors[0]))

conn = connect(PROFILE, cfg["lakebase_instance"], cfg["lakebase_database"])
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
conn.execute("DROP TABLE IF EXISTS chunk_vectors")
conn.execute(
    f"""CREATE TABLE chunk_vectors (
        chunk_id text PRIMARY KEY, name text, heading text, text text, vector vector({DIM}))"""
)
with conn.cursor() as cur:
    cur.executemany(
        "INSERT INTO chunk_vectors VALUES (%s, %s, %s, %s, %s::vector)",
        [(r.chunk_id, r.name, r.heading, r.text, to_pg(v)) for r, v in zip(rows, vectors)],
    )
conn.execute("CREATE INDEX ON chunk_vectors USING hnsw (vector vector_cosine_ops)")

QUESTIONS = [  # (question, package we expect)
    ("How do I send an HTTP request with async support?", "httpx"),
    ("How do I validate data with type hints and models?", "pydantic"),
    ("How do I log messages with a simple logger?", "loguru"),
]
for q, expected in QUESTIONS:
    qv = to_pg(embed([q], client)[0])
    hits = conn.execute(
        "SELECT name, heading, left(text, 100), vector <=> %s::vector AS dist "
        "FROM chunk_vectors ORDER BY dist LIMIT 3",
        (qv,),
    ).fetchall()
    print(f"\nQ: {q}  (expected: {expected})")
    for h in hits:
        print(f"  {h[3]:.3f} {h[0]} | {h[1]} | {h[2]!r}")
