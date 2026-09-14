from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_app_starts_and_health_ok():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_exposes_three_frozen_business_endpoints():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]

    assert "/api/v1/pricing/score" in paths
    assert "post" in paths["/api/v1/pricing/score"]

    assert "/api/v1/ocr/extract" in paths
    assert "post" in paths["/api/v1/ocr/extract"]

    assert "/api/v1/receipt/analyze" in paths
    assert "post" in paths["/api/v1/receipt/analyze"]


def test_pricing_score_requires_api_key():
    resp = client.post(
        "/api/v1/pricing/score",
        json={"name": "Wireless Mouse", "category": "Computer Accessories", "price": 2499.0},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["error"]


def test_pricing_score_stub_returns_not_implemented_with_valid_key():
    resp = client.post(
        "/api/v1/pricing/score",
        json={"name": "Wireless Mouse", "category": "Computer Accessories", "price": 2499.0},
        headers={"X-API-Key": "dev-local-key"},
    )
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "NOT_IMPLEMENTED"


def test_error_response_shape_matches_frozen_contract():
    resp = client.post(
        "/api/v1/ocr/extract",
        json={"object_key": "org/1/x.pdf"},
        headers={"X-API-Key": "dev-local-key"},
    )
    body = resp.json()
    assert set(body["error"].keys()) == {"code", "message", "request_id", "details"}
