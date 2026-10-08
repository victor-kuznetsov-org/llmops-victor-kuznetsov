# Databricks notebook source
from pathlib import Path

import yaml
from databricks.connect import DatabricksSession
from pyspark.sql import Row

from pkgscout.chunks import split_by_headings

CONFIG = (
    Path(__file__).resolve().parents[2] / "project_config.yml"
    if "__file__" in globals()
    else Path("project_config.yml")
)
cfg = yaml.safe_load(CONFIG.read_text())["dev"]
base = f"{cfg['catalog']}.{cfg['schema']}"
spark = DatabricksSession.builder.profile("student-victor-kuznetsov").serverless(True).getOrCreate()

rows = []
for r in spark.table(f"{base}.pypi_packages").select("name", "description").collect():
    for i, c in enumerate(split_by_headings(r.description)):
        rows.append(
            Row(
                chunk_id=f"{r.name}_{i}",
                name=r.name,
                chunk_index=i,
                heading=c["heading"],
                text=c["text"],
            )
        )

table = f"{base}.package_chunks"
spark.createDataFrame(rows).write.mode("overwrite").option(
    "delta.enableChangeDataFeed", "true"
).saveAsTable(table)
spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
print(table, spark.table(table).count())
