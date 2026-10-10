# Databricks notebook source
from pathlib import Path
from uuid import uuid4

import psycopg
import yaml
from databricks.connect import DatabricksSession
from databricks_openai import DatabricksOpenAI

from pkgscout.agent import SYSTEM_PROMPT, run_turn
from pkgscout.memory import ChatMemory
from pkgscout.tools import make_search_tool, make_version_tool
from pkgscout.vectors import connect

PROFILE = "student-victor-kuznetsov"
CONFIG = (
    Path(__file__).resolve().parents[2] / "project_config.yml"
    if "__file__" in globals()
    else Path("project_config.yml")
)
cfg = yaml.safe_load(CONFIG.read_text())["dev"]

spark = DatabricksSession.builder.profile(PROFILE).serverless(True).getOrCreate()
client = DatabricksOpenAI(use_ai_gateway=True)
tools = [make_version_tool(spark, f"{cfg['catalog']}.{cfg['schema']}.pypi_packages")]
memory = None
try:
    conn = connect(PROFILE, cfg["lakebase_instance"], cfg["lakebase_database"])
    tools.insert(0, make_search_tool(conn, client))
    memory = ChatMemory(conn)
except (OSError, psycopg.OperationalError) as e:  # the sandbox cannot reach Lakebase on port 5432
    print("Lakebase unreachable, running with the version tool only:", e)

# 3.1: each tool called once
for t in tools:
    args = (
        {"query": "send an async HTTP request"} if t.name == "search_chunks" else {"name": "httpx"}
    )
    print(t.name, "->", t.exec_fn(**args)[:300])

# 3.3 + 3.4: session one, a few turns, saved to Lakebase after each turn
sid = f"pkgscout-{uuid4()}"
messages = [{"role": "system", "content": SYSTEM_PROMPT}]
for q in [
    "How do I make async HTTP requests in Python?",
    "What is the latest version of the package you just named?",
    "And the latest version of pydantic?",
]:
    user = {"role": "user", "content": q}
    messages.append(user)
    new = run_turn(client, cfg["llm_endpoint"], tools, messages)
    if memory:
        memory.save(sid, [user, *new])
    print("\nQ:", q, "\nA:", new[-1]["content"])
    print("tools:", [c["function"]["name"] for m in new for c in m.get("tool_calls", [])])

# 3.4: second session loads the saved messages and continues
if memory is None:
    raise SystemExit("no Lakebase: 3.4 not run")
loaded = memory.load(sid)
print("\nloaded", len(loaded), "messages")
loaded.append({"role": "user", "content": "Which package did I ask about first?"})
new = run_turn(client, cfg["llm_endpoint"], tools, loaded)
print("A:", new[-1]["content"])
