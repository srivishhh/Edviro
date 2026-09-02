from __future__ import annotations

import logging
import os
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.schemas.sns import (
    SNSDigitalTwinData,
    SNSEventPayload,
    SNSGenericEventRequest,
    SNSRelatedSensorData,
)

logger = logging.getLogger(__name__)


class InvestigationProvider(Protocol):
    def create_investigation(self, *, context: dict, investigation_id: str):
        ...


def create_test_hvac_payload() -> SNSEventPayload:
    """Builds the canonical HVAC-007 anomaly payload for SNS Workbench testing."""
    return SNSEventPayload(
        investigation_id="INV-001",
        facility_id="FAC-001",
        facility_name="School Building A",
        facility_type="school",
        building_id="BLDG-001",
        floor_id="FLOOR-02",
        asset_id="HVAC-007",
        asset_name="AHU Floor 2",
        sensor_id="TEMP-007",
        metric="temperature",
        current_value=31.8,
        unit="C",
        expected_min=20.0,
        expected_max=26.0,
        timestamp="2026-09-02T11:00:00",
        historical_telemetry=[23.2, 23.8, 24.1, 24.5, 25.0],
        related_sensor_data=SNSRelatedSensorData(
            airflow=42.0,
            expected_airflow=70.0,
            fan_status="normal",
            energy_kw=12.4,
            expected_energy_kw=8.1,
        ),
        digital_twin=SNSDigitalTwinData(
            facility="School Building A",
            building="Building A",
            floor="Floor 2",
            asset="HVAC-007",
            asset_type="AHU",
            relationships=[
                "HVAC-007 -> TEMP-007",
                "HVAC-007 -> AIRFLOW-007",
                "HVAC-007 -> FAN-007",
            ],
        ),
    )


def normalize_generic_event(event_req: SNSGenericEventRequest) -> SNSEventPayload:
    """Normalizes a generic incoming event request into a validated SNSEventPayload."""
    default_payload = create_test_hvac_payload()
    data = default_payload.model_dump()

    req_dict = event_req.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in req_dict.items():
        if key == "related_sensor_data" and isinstance(value, dict):
            data["related_sensor_data"].update(value)
        elif key == "digital_twin" and isinstance(value, dict):
            data["digital_twin"].update(value)
        else:
            data[key] = value

    return SNSEventPayload.model_validate(data)


class SNSWorkbenchClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        agent_id: str | None = None,
        webhook_test_url: str | None = None,
    ):
        self.base_url = base_url or settings.sns_workbench_url or os.getenv("SNS_WORKBENCH_URL", "https://sns-workbench.example.invalid")
        self.api_key = api_key or settings.sns_api_key or os.getenv("SNS_API_KEY")
        self.agent_id = agent_id or settings.sns_agent_id or os.getenv("SNS_AGENT_ID", "facility-xray-demo")
        self.webhook_test_url = (
            webhook_test_url
            or settings.sns_webhook_test_url
            or os.getenv("SNS_WEBHOOK_TEST_URL")
        )

    def create_investigation(self, *, context: dict, investigation_id: str):
        return {
            "investigation_id": investigation_id,
            "status": "PENDING",
            "provider": "sns_workbench",
            "asset_id": context["asset"]["id"],
            "alert_id": context["alert"]["id"],
            "agent_id": self.agent_id,
        }

    def run_investigation(self, *, investigation_id: str):
        return {
            "investigation_id": investigation_id,
            "status": "RUNNING",
            "provider": "sns_workbench",
            "agent_id": self.agent_id,
        }

    def get_investigation_result(self, *, investigation_id: str):
        return {
            "investigation_id": investigation_id,
            "status": "COMPLETED",
            "provider": "sns_workbench",
            "agent_id": self.agent_id,
        }

    def send_webhook_event(
        self,
        payload: SNSEventPayload | dict | Any,
        mode: str = "test",
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Sends a structured payload to the configured SNS Workbench Webhook Trigger.
        Destination URL is strictly resolved from server configuration.
        """
        if webhook_url:
            target_url = webhook_url
        elif mode == "production":
            target_url = settings.sns_webhook_production_url or os.getenv("SNS_WEBHOOK_PRODUCTION_URL")
        else:
            target_url = self.webhook_test_url or settings.sns_webhook_test_url or os.getenv("SNS_WEBHOOK_TEST_URL")

        if isinstance(payload, SNSEventPayload):
            payload_obj = payload
        elif isinstance(payload, dict):
            payload_obj = SNSEventPayload.model_validate(payload)
        else:
            payload_obj = SNSEventPayload.model_validate(payload)

        investigation_id = payload_obj.investigation_id
        asset_id = payload_obj.asset_id

        if not target_url or not target_url.strip():
            logger.warning("SNS Webhook URL is not configured for mode=%s.", mode)
            return {
                "status": "failed",
                "error": "SNS_WEBHOOK_TEST_URL is not configured" if mode == "test" else "SNS_WEBHOOK_PRODUCTION_URL is not configured",
                "sns_status_code": None,
                "investigation_id": investigation_id,
            }

        # Validate URL scheme (must be https unless localhost for local dev/testing)
        lower_url = target_url.lower()
        if not lower_url.startswith("https://") and not lower_url.startswith("http://localhost") and not lower_url.startswith("http://127.0.0.1"):
            logger.error("SNS Webhook URL rejected: Insecure HTTP protocol not permitted for remote endpoints.")
            return {
                "status": "failed",
                "error": "Insecure webhook URL: HTTPS is required for remote endpoints.",
                "sns_status_code": None,
                "investigation_id": investigation_id,
            }

        data = payload_obj.model_dump(mode="json")
        logger.info("SNS request started: investigation_id=%s, asset_id=%s, mode=%s", investigation_id, asset_id, mode)

        explicit_timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

        try:
            with httpx.Client(timeout=explicit_timeout) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["X-API-Key"] = self.api_key

                response = client.post(
                    target_url,
                    json=data,
                    headers=headers,
                )

            if 200 <= response.status_code < 300:
                logger.info("SNS response success status %s for investigation_id=%s", response.status_code, investigation_id)
                return {
                    "status": "sent",
                    "sns_status_code": response.status_code,
                    "investigation_id": investigation_id,
                }
            else:
                logger.error(
                    "SNS response failure status %s for investigation_id=%s",
                    response.status_code,
                    investigation_id,
                )
                return {
                    "status": "failed",
                    "error": f"SNS webhook request failed with status {response.status_code}",
                    "sns_status_code": response.status_code,
                    "investigation_id": investigation_id,
                }

        except httpx.TimeoutException:
            logger.error("SNS request timed out for investigation_id=%s", investigation_id)
            return {
                "status": "failed",
                "error": "SNS webhook request timed out",
                "sns_status_code": None,
                "investigation_id": investigation_id,
            }
        except httpx.RequestError as exc:
            logger.error("SNS connection failure for investigation_id=%s: %s", investigation_id, exc)
            return {
                "status": "failed",
                "error": f"SNS webhook connection failed: {exc}",
                "sns_status_code": None,
                "investigation_id": investigation_id,
            }
        except Exception as exc:
            logger.error("Unexpected error during SNS webhook dispatch for investigation_id=%s: %s", investigation_id, exc)
            return {
                "status": "failed",
                "error": f"SNS webhook dispatch error: {exc}",
                "sns_status_code": None,
                "investigation_id": investigation_id,
            }

