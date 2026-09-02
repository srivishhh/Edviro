from __future__ import annotations

import os
from typing import Protocol


class InvestigationProvider(Protocol):
    def create_investigation(self, *, context: dict, investigation_id: str):
        ...


class SNSWorkbenchClient:
    def __init__(self, *, base_url: str | None = None, api_key: str | None = None, agent_id: str | None = None):
        self.base_url = base_url or os.getenv("SNS_WORKBENCH_URL", "https://sns-workbench.example.invalid")
        self.api_key = api_key or os.getenv("SNS_API_KEY")
        self.agent_id = agent_id or os.getenv("SNS_AGENT_ID", "facility-xray-demo")

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
