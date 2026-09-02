from __future__ import annotations

from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.integrations.sns_workbench import (
    SNSWorkbenchClient,
    create_test_hvac_payload,
    normalize_generic_event,
)
from app.schemas.sns import SNSEventPayload, SNSGenericEventRequest
from main import app

client = TestClient(app)


def test_1_sns_configuration_loaded(monkeypatch):
    """Test 1: Verify SNS_WEBHOOK_TEST_URL is loaded through Settings/config."""
    test_url = "https://api.agents.snsihub.ai/webhook-test/mock-test-id"
    monkeypatch.setenv("SNS_WEBHOOK_TEST_URL", test_url)

    fresh_settings = Settings()
    assert fresh_settings.sns_webhook_test_url == test_url

    sns_client = SNSWorkbenchClient(webhook_test_url=test_url)
    assert sns_client.webhook_test_url == test_url


def test_2_payload_validation():
    """Test 2: Verify Pydantic payload model validates schema and defaults."""
    payload = create_test_hvac_payload()

    assert payload.investigation_id == "INV-001"
    assert payload.facility_id == "FAC-001"
    assert payload.asset_id == "HVAC-007"
    assert payload.sensor_id == "TEMP-007"
    assert payload.metric == "temperature"
    assert payload.current_value == 31.8
    assert payload.unit == "C"
    assert payload.expected_min == 20.0
    assert payload.expected_max == 26.0
    assert payload.historical_telemetry == [23.2, 23.8, 24.1, 24.5, 25.0]
    assert payload.related_sensor_data.airflow == 42.0
    assert payload.related_sensor_data.energy_kw == 12.4
    assert "HVAC-007 -> TEMP-007" in payload.digital_twin.relationships

    # Validate normalization of generic event
    generic_req = SNSGenericEventRequest(
        investigation_id="INV-999",
        asset_id="HVAC-002",
        sensor_id="TEMP-002",
        metric="temperature",
        current_value=28.4,
    )
    normalized = normalize_generic_event(generic_req)
    assert normalized.investigation_id == "INV-999"
    assert normalized.asset_id == "HVAC-002"
    assert normalized.current_value == 28.4


def test_3_sns_client_sends_correct_payload():
    """Test 3: Verify SNS client sends correct JSON payload via HTTP POST (mocked)."""
    test_url = "https://api.agents.snsihub.ai/webhook-test/mock-endpoint"
    sns_client = SNSWorkbenchClient(webhook_test_url=test_url)
    payload = create_test_hvac_payload()

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = sns_client.send_webhook_event(payload)

        assert mock_post.called
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == test_url
        assert call_kwargs["json"]["investigation_id"] == "INV-001"
        assert call_kwargs["json"]["asset_id"] == "HVAC-007"
        assert call_kwargs["json"]["metric"] == "temperature"
        assert call_kwargs["json"]["current_value"] == 31.8

        assert result["status"] == "sent"
        assert result["sns_status_code"] == 200
        assert result["investigation_id"] == "INV-001"


def test_4_sns_timeout_handled():
    """Test 4: Verify timeout exception is caught and returns structured failure."""
    test_url = "https://api.agents.snsihub.ai/webhook-test/mock-timeout"
    sns_client = SNSWorkbenchClient(webhook_test_url=test_url)
    payload = create_test_hvac_payload()

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Request timed out")):
        result = sns_client.send_webhook_event(payload)

        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()
        assert result["sns_status_code"] is None
        assert result["investigation_id"] == "INV-001"


def test_5_sns_http_error_handled():
    """Test 5: Verify HTTP 500 error from SNS is caught and returns structured failure."""
    test_url = "https://api.agents.snsihub.ai/webhook-test/mock-error"
    sns_client = SNSWorkbenchClient(webhook_test_url=test_url)
    payload = create_test_hvac_payload()

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 502

    with patch("httpx.Client.post", return_value=mock_response):
        result = sns_client.send_webhook_event(payload)

        assert result["status"] == "failed"
        assert "502" in result["error"]
        assert result["sns_status_code"] == 502
        assert result["investigation_id"] == "INV-001"


def test_6_test_endpoint_responses():
    """Test 6: Verify POST /api/v1/integrations/sns/test and /events endpoints."""
    # Scenario A: Success
    with patch("app.integrations.sns_workbench.SNSWorkbenchClient.send_webhook_event") as mock_send:
        mock_send.return_value = {
            "status": "sent",
            "sns_status_code": 200,
            "investigation_id": "INV-001",
        }

        response = client.post("/api/v1/integrations/sns/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["sns_status_code"] == 200
        assert data["investigation_id"] == "INV-001"

    # Scenario B: Missing URL / Failure
    with patch("app.integrations.sns_workbench.SNSWorkbenchClient.send_webhook_event") as mock_send:
        mock_send.return_value = {
            "status": "failed",
            "error": "SNS_WEBHOOK_TEST_URL is not configured",
            "sns_status_code": None,
            "investigation_id": "INV-001",
        }

        response = client.post("/api/v1/integrations/sns/test")
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "failed"
        assert "SNS_WEBHOOK_TEST_URL" in data["error"]

    # Scenario C: Forward generic event
    with patch("app.integrations.sns_workbench.SNSWorkbenchClient.send_webhook_event") as mock_send:
        mock_send.return_value = {
            "status": "sent",
            "sns_status_code": 200,
            "investigation_id": "INV-002",
        }

        event_payload = {
            "investigation_id": "INV-002",
            "asset_id": "HVAC-007",
            "sensor_id": "TEMP-007",
            "metric": "temperature",
            "current_value": 31.8,
        }
        response = client.post("/api/v1/integrations/sns/events", json=event_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["investigation_id"] == "INV-002"
