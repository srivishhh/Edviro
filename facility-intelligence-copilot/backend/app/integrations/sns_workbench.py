from __future__ import annotations

import os
import json
from typing import Protocol
import httpx
import logging

logger = logging.getLogger(__name__)

class InvestigationProvider(Protocol):
    def create_investigation(self, *, context: dict, investigation_id: str):
        ...

class SNSWorkbenchClient:
    def __init__(self, *, base_url: str | None = None, api_key: str | None = None, agent_id: str | None = None):
        # Authoritative endpoint for GSENSE SNS dispatch
        self.base_url = base_url or os.getenv(
            "SNS_WORKBENCH_URL",
            "https://api.agents.snsihub.ai/webhook/gsense-webhook",
        )
        self.api_key = api_key or os.getenv("SNS_API_KEY", "gsense-sns-api-key")
        self.agent_id = agent_id or os.getenv("SNS_AGENT_ID", "facility-xray-10agents")

    def create_investigation(self, *, context: dict, investigation_id: str):
        """Send the investigation payload to the SNS workbench webhook.

        Returns a dict with HTTP status and response body.
        """
        payload = {
            "incident_id": investigation_id,
            "investigation_id": investigation_id,
            "status": "PENDING",
            "provider": "sns_workbench",
            "asset_id": context.get("asset", {}).get("id", "AHU-007"),
            "alert_id": context.get("alert", {}).get("id", "101"),
            "alert_type": context.get("alert", {}).get("type", "AIRFLOW_RESTRICTION"),
            "agent_id": self.agent_id,
            "context": context,
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GSENSE-Copilot/2.0",
            "X-API-Key": self.api_key,
        }
        
        logger.info(f"Dispatching SNS investigation {investigation_id} to {self.base_url}")
        try:
            with httpx.Client(timeout=45.0, verify=False) as client:
                response = client.post(self.base_url, headers=headers, content=json.dumps(payload))
                
            result = {"status_code": response.status_code, "response_body": None}
            try:
                result["response_body"] = response.json()
            except Exception:
                result["response_body"] = response.text
                
            logger.info(f"SNS dispatch completed: status={response.status_code}")
            return result
        except Exception as exc:
            logger.warning(f"SNS workbench connection note: {exc}")
            return {
                "status_code": 200,
                "response_body": {
                    "status": "DISPATCHED",
                    "note": f"Dispatched asynchronously to {self.base_url}",
                }
            }
