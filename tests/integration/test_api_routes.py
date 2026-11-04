import pytest


def test_health_endpoint_public(test_client):
    """Health endpoint must be accessible without API key."""
    res = test_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "X-Request-ID" in res.headers
    assert "X-Response-Time-Ms" in res.headers


def test_list_meters_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/meters?limit=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) == 3
    assert data["meta"]["total"] == 3
    assert data["meta"]["page"] == 1


def test_get_meter_detail_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/meters/J100000", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["meter_id"] == "J100000"
    assert data["data"]["hierarchy"]["zone"]["code"] == "Z-01"


def test_get_meter_not_found(test_client, auth_headers):
    res = test_client.get("/api/v1/meters/NON_EXISTENT_ID", headers=auth_headers)
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_list_transformers_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/transformers", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    assert data["data"][0]["code"] == "DT-001"


def test_get_transformer_detail_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/transformers/DT-001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["code"] == "DT-001"
    assert len(data["data"]["meters"]) == 2


def test_summary_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total_meters"] == 3
    assert data["data"]["total_transformers"] == 2


def test_hierarchy_endpoint(test_client, auth_headers):
    res = test_client.get("/api/v1/hierarchy", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total_zones"] == 1
    assert data["data"]["total_meters"] == 3
