from fastapi.testclient import TestClient

from app.api.dependencies import get_s3_service
from app.main import app
from app.services.s3_service import UnimplementedS3Service

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
    # This test checks only the HTTP-level error envelope shape, not real
    # S3 behavior — that has its own coverage in test_s3_service.py. Swap
    # in the stub so this test doesn't depend on AWS config being present.
    app.dependency_overrides[get_s3_service] = lambda: UnimplementedS3Service()
    try:
        resp = client.post(
            "/api/v1/ocr/extract",
            json={"object_key": "org/1/x.pdf"},
            headers={"X-API-Key": "dev-local-key"},
        )
        body = resp.json()
        assert set(body["error"].keys()) == {"code", "message", "request_id", "details"}
    finally:
        app.dependency_overrides.clear()


def test_schema_validation_error_also_uses_frozen_envelope():
    resp = client.post(
        "/api/v1/ocr/extract",
        json={"object_key": ""},
        headers={"X-API-Key": "dev-local-key"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert set(body["error"].keys()) == {"code", "message", "request_id", "details"}
    assert body["error"]["code"] == "VALIDATION_ERROR"
