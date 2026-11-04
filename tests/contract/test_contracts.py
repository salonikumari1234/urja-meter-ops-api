import json
from pathlib import Path
import pytest


def test_openapi_json_is_valid():
    openapi_path = Path(__file__).resolve().parent.parent.parent / "openapi.json"
    assert openapi_path.exists(), "openapi.json must exist in project root"

    with open(openapi_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    assert "openapi" in spec
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
    assert "/api/v1/health" in spec["paths"]
    assert "/api/v1/meters" in spec["paths"]
    assert "/api/v1/meters/{meter_id}" in spec["paths"]
    assert "/api/v1/transformers" in spec["paths"]
    assert "/api/v1/hierarchy" in spec["paths"]
    assert "/api/v1/summary" in spec["paths"]


def test_standard_response_envelope_contract(test_client, auth_headers):
    res = test_client.get("/api/v1/meters", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "success" in data
    assert "data" in data
    assert "meta" in data
    assert isinstance(data["success"], bool)
    assert isinstance(data["data"], list)
    assert "timestamp" in data["meta"]
    assert "source" in data["meta"]
    assert data["meta"]["source"] == "urja-ops"
