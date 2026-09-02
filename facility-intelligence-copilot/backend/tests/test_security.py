from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.auth import Role
from app.core.config import Settings, settings
from app.integrations.sns_workbench import SNSWorkbenchClient, create_test_hvac_payload
from main import app

client = TestClient(app)


def test_1_missing_api_key_when_auth_enabled(monkeypatch):
    """Test 1: Missing API key returns HTTP 401 when API_AUTH_ENABLED=true."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", "secret-admin-key:ADMIN")

    response = client.post("/api/v1/assets", json={"asset_code": "NEW-001", "name": "New Asset", "asset_type": "HVAC", "status": "healthy", "health_score": 100.0, "building_id": 1, "floor_id": 1})
    assert response.status_code == 401
    assert "Authentication required" in response.json()["error"]["message"]


def test_2_invalid_api_key_returns_401(monkeypatch):
    """Test 2: Invalid API key returns HTTP 401."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", "secret-admin-key:ADMIN")

    response = client.post(
        "/api/v1/assets",
        headers={"Authorization": "Bearer wrong-key"},
        json={"asset_code": "NEW-001", "name": "New Asset", "asset_type": "HVAC", "status": "healthy", "health_score": 100.0, "building_id": 1, "floor_id": 1},
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["error"]["message"]


def test_3_valid_api_key_allowed(monkeypatch):
    """Test 3: Valid API key allows operation."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", "valid-admin-key:ADMIN")

    response = client.get(
        "/api/v1/assets",
        headers={"X-API-Key": "valid-admin-key"},
    )
    assert response.status_code == 200


def test_4_viewer_cannot_mutate_asset(monkeypatch):
    """Test 4: VIEWER role cannot create/modify assets (HTTP 403)."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", "viewer-key:VIEWER")

    response = client.post(
        "/api/v1/assets",
        headers={"Authorization": "Bearer viewer-key"},
        json={"asset_code": "NEW-001", "name": "New Asset", "asset_type": "HVAC", "status": "healthy", "health_score": 100.0, "building_id": 1, "floor_id": 1},
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["error"]["message"]


def test_5_invalid_alert_status_rejected():
    """Test 5: Invalid alert status is rejected with HTTP 422."""
    response = client.patch(
        "/api/v1/alerts/101",
        json={"status": "INVALID_CUSTOM_STATUS"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_6_oversized_telemetry_rejected():
    """Test 6: Out of bound telemetry value (e.g. temperature > 200C) is rejected."""
    payload = {
        "event_id": "evt-oversized",
        "event_type": "telemetry",
        "asset_id": 7,
        "timestamp": "2026-09-02T11:00:00Z",
        "temperature": 9999.0,  # exceeds 200.0 max
        "pressure": 3.5,
        "airflow": 90.0,
        "energy_kw": 5.0,
    }
    response = client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_7_invalid_sns_signature_rejected(monkeypatch):
    """Test 7: Inbound webhook with invalid HMAC signature returns HTTP 401."""
    secret = "test-signing-secret"
    monkeypatch.setattr(settings, "sns_webhook_signing_secret", secret)

    raw_body = b'{"event":"test"}'
    response = client.post(
        "/api/v1/integrations/sns/webhook",
        content=raw_body,
        headers={"X-SNS-Signature": "sha256=invalidhex0000"},
    )
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["error"]["message"]


def test_8_missing_sns_signature_rejected_when_configured(monkeypatch):
    """Test 8: Missing signature header returns HTTP 401 when secret is configured."""
    secret = "test-signing-secret"
    monkeypatch.setattr(settings, "sns_webhook_signing_secret", secret)

    response = client.post(
        "/api/v1/integrations/sns/webhook",
        json={"event": "test"},
    )
    assert response.status_code == 401
    assert "Missing X-SNS-Signature" in response.json()["error"]["message"]


def test_9_valid_sns_signature_accepted(monkeypatch):
    """Test 9: Valid HMAC-SHA256 signature is accepted (HTTP 200)."""
    secret = "test-signing-secret"
    monkeypatch.setattr(settings, "sns_webhook_signing_secret", secret)

    raw_body = b'{"event":"test_alert"}'
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/integrations/sns/webhook",
        content=raw_body,
        headers={"X-SNS-Signature": f"sha256={sig}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_10_sns_timeout_handled_safely():
    """Test 10: SNS timeout returns structured failure without crashing."""
    sns_client = SNSWorkbenchClient(webhook_test_url="https://api.agents.snsihub.ai/webhook-test/demo")
    payload = create_test_hvac_payload()

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timeout")):
        res = sns_client.send_webhook_event(payload)
        assert res["status"] == "failed"
        assert "timed out" in res["error"].lower()


def test_11_sns_500_handled_safely():
    """Test 11: SNS HTTP 500 error returns structured failure with status code."""
    sns_client = SNSWorkbenchClient(webhook_test_url="https://api.agents.snsihub.ai/webhook-test/demo")
    payload = create_test_hvac_payload()

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 500

    with patch("httpx.Client.post", return_value=mock_resp):
        res = sns_client.send_webhook_event(payload)
        assert res["status"] == "failed"
        assert res["sns_status_code"] == 500


def test_12_credentials_never_appear_in_response(monkeypatch):
    """Test 12: API keys / credentials are never returned in responses."""
    monkeypatch.setattr(settings, "sns_api_key", "super-secret-key-12345")
    sns_client = SNSWorkbenchClient(webhook_test_url="https://api.agents.snsihub.ai/webhook-test/demo")
    payload = create_test_hvac_payload()

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200

    with patch("httpx.Client.post", return_value=mock_resp):
        res = sns_client.send_webhook_event(payload)
        assert "super-secret-key-12345" not in str(res)


def test_13_security_headers_present():
    """Test 13: Security headers (nosniff, DENY, no-referrer) are injected on responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert "X-Request-ID" in response.headers


def test_14_non_existent_asset_returns_404():
    """Test 14: Accessing a non-existent asset ID returns HTTP 404."""
    response = client.get("/api/v1/assets/999999")
    assert response.status_code == 404


def test_15_health_endpoint_public_and_clean():
    """Test 15: /health and /api/v1/system/status remain public and do not leak internals."""
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok", "service": "backend"}

    res_status = client.get("/api/v1/system/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "backend" in data
    assert "database" in data
    # Ensure no passwords or connection strings are leaked
    assert "password" not in str(data).lower()
    assert "postgresql://" not in str(data).lower()
