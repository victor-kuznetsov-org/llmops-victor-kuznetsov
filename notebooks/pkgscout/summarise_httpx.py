# Databricks notebook source
from pkgscout.ingest import fetch_package
from pkgscout.summarise import get_client, llm_endpoint, summarise

pkg = fetch_package("httpx")
text, usage = summarise(
    get_client(), llm_endpoint(), "httpx", pkg["description"]
)
print(text)
print(usage)
