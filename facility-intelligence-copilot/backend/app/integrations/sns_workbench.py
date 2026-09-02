from __future__ import annotations

import os
import httpx
from typing import Protocol, Dict, Any


class InvestigationProvider(Protocol):
    def send_facility_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Send facility event to the configured intelligence layer."""
        ...


class SNSWorkbenchClient:
    def __init__(self, *, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.getenv(
            "SNS_WORKBENCH_WEBHOOK_URL",
            "{{PASTE_THE_PRODUCTION_WEBHOOK_URL_HERE}}"
        )

    def send_facility_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if not self.webhook_url or self.webhook_url == "{{PASTE_THE_PRODUCTION_WEBHOOK_URL_HERE}}":
            print("WARNING: SNS_WORKBENCH_WEBHOOK_URL is not configured properly.")
            # For development safety, return a mock or raise error based on preference
            pass

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.webhook_url, json=event)
                response.raise_for_status()
                result = response.json()
                if not result:
                    return self._fallback_malformed_response(event, "Empty response from SNS Workbench")
                return result
        except httpx.TimeoutException:
            return self._fallback_error_response(event, "SNS Workbench timeout")
        except httpx.HTTPStatusError as exc:
            return self._fallback_error_response(event, f"HTTP error {exc.response.status_code}")
        except Exception as exc:
            return self._fallback_error_response(event, f"Unexpected error: {str(exc)}")
            
    def _fallback_error_response(self, event: Dict[str, Any], reason: str) -> Dict[str, Any]:
        return {
            "investigation_id": event.get("investigation_id", "ERROR"),
            "event_id": event.get("event_id", ""),
            "status": "FAILED",
            "event_class": "UNKNOWN",
            "incident_assurance": {
                "decision": "REQUIRES_REVIEW",
                "confidence": 0.0,
                "notification_allowed": False
            },
            "diagnostic_reasoning": {"error": reason}
        }
        
    def _fallback_malformed_response(self, event: Dict[str, Any], reason: str) -> Dict[str, Any]:
        return self._fallback_error_response(event, reason)
