import pytest


def test_missing_api_key_rejected(test_client):
    res = test_client.get("/api/v1/meters")
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "missing" in data["error"]["message"].lower()


def test_invalid_api_key_rejected(test_client):
    res = test_client.get("/api/v1/meters", headers={"X-API-Key": "completely_wrong_key"})
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "invalid" in data["error"]["message"].lower()


def test_invalid_pagination_bounds_rejected(test_client, auth_headers):
    # limit > 100 must fail with 422
    res = test_client.get("/api/v1/meters?limit=9999", headers=auth_headers)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_PARAMETER"

    # page < 1 must fail with 422
    res_page = test_client.get("/api/v1/meters?page=0", headers=auth_headers)
    assert res_page.status_code == 422
    data_page = res_page.json()
    assert data_page["success"] is False
    assert data_page["error"]["code"] == "INVALID_PARAMETER"


def test_invalid_sort_order_rejected(test_client, auth_headers):
    # sort_order must be asc or desc
    res = test_client.get("/api/v1/meters?sort_order=malicious_sqli", headers=auth_headers)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_PARAMETER"


def test_headers_never_leak_upstream_secrets(test_client, auth_headers):
    res = test_client.get("/api/v1/meters/J100000", headers=auth_headers)
    assert res.status_code == 200
    res_text = res.text.lower()
    # Check that secrets or session cookies are never leaked
    assert "better-auth.session_token" not in res_text
    assert "password" not in res_text
