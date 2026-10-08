"""Read popular packages from the PyPI JSON API."""

import gzip
import http.client
import json
import time
import urllib.request

PACKAGES = [
    "requests", "numpy", "pandas", "httpx", "pydantic", "flask", "django", "fastapi",
    "scipy", "matplotlib", "pytest", "sqlalchemy", "boto3", "click", "rich", "pillow",
    "scikit-learn", "uvicorn", "jinja2", "pyyaml", "openai", "mlflow", "loguru", "typer",
    "beautifulsoup4",
]  # fmt: skip


def fetch_package(name: str, retries: int = 4) -> dict:
    """Fetch one package from https://pypi.org/pypi/<name>/json and keep the fields we need."""
    req = urllib.request.Request(
        f"https://pypi.org/pypi/{name}/json", headers={"Accept-Encoding": "gzip"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            break
        except (http.client.IncompleteRead, OSError):
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)
    data = json.loads(raw)
    info = data["info"]
    files = data.get("urls") or []
    return {
        "name": name,
        "version": info.get("version"),
        "summary": info.get("summary"),
        "release_date": files[0].get("upload_time_iso_8601") if files else None,
        "description": info.get("description"),
    }


def fetch_all(names: list[str] | None = None) -> list[dict]:
    """Fetch every package; one that keeps failing is skipped and reported."""
    rows = []
    for n in names or PACKAGES:
        try:
            rows.append(fetch_package(n, retries=6))
        except (http.client.HTTPException, OSError) as e:
            print(f"skipped {n}: {e!r}")
    return rows
