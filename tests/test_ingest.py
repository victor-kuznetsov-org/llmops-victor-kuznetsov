import io
import json
from unittest.mock import MagicMock, patch

from pkgscout.ingest import PACKAGES, fetch_package


def test_package_list_size() -> None:
    assert 20 <= len(PACKAGES) <= 30


def test_fetch_package_keeps_the_fields() -> None:
    payload = {
        "info": {"version": "1.0", "summary": "s", "description": "d"},
        "urls": [{"upload_time_iso_8601": "2024-01-01T00:00:00Z"}],
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.headers = {}
    resp.__enter__.return_value = resp
    with patch("urllib.request.urlopen", return_value=resp):
        row = fetch_package("x")
    assert row == {
        "name": "x",
        "version": "1.0",
        "summary": "s",
        "release_date": "2024-01-01T00:00:00Z",
        "description": "d",
    }
    assert io  # keep import used
