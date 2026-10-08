# Databricks notebook source
from pathlib import Path
from statistics import mean

import yaml
from databricks.connect import DatabricksSession

from pkgscout.chunks import fixed_windows, split_by_headings

CONFIG = (
    Path(__file__).resolve().parents[2] / "project_config.yml"
    if "__file__" in globals()
    else Path("project_config.yml")
)
cfg = yaml.safe_load(CONFIG.read_text())["dev"]
base = f"{cfg['catalog']}.{cfg['schema']}"
spark = DatabricksSession.builder.profile("student-victor-kuznetsov").serverless(True).getOrCreate()

descriptions = [r.description or "" for r in spark.table(f"{base}.pypi_packages").collect()]
heading = [len(c["text"]) for d in descriptions for c in split_by_headings(d)]
windows = [len(w) for d in descriptions for w in fixed_windows(d, 800, 100)]

for label, sizes in [("headings", heading), ("fixed 800/100", windows)]:
    print(f"{label:14} count={len(sizes):5} mean={mean(sizes):8.1f} longest={max(sizes)}")
# Decision: keep the heading chunks (package_chunks).
