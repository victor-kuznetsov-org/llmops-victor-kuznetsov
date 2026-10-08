# Databricks notebook source
from pathlib import Path

import yaml
from databricks.connect import DatabricksSession
from pyspark.sql import functions as F

from pkgscout.ingest import fetch_all

CONFIG = Path(__file__).resolve().parents[2] / "project_config.yml" if "__file__" in globals() else Path("project_config.yml")
cfg = yaml.safe_load(open(CONFIG))["dev"]
table = f"{cfg['catalog']}.{cfg['schema']}.pypi_packages"

spark = DatabricksSession.builder.profile("student-victor-kuznetsov").serverless(True).getOrCreate()

rows = fetch_all()
df = spark.createDataFrame(rows).withColumn("release_date", F.to_timestamp("release_date"))
df.select("name", "version", "summary", "release_date", "description").write.mode(
    "overwrite"
).saveAsTable(table)
print(table, spark.table(table).count())
