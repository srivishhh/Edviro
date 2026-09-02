from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.xray.investigation import InvestigationContextBuilder
from app.xray.models import Evidence, XRayInvestigationResult


class InvestigationProvider:
    def create_investigation(self, *, context: dict, investigation_id: str):
        raise NotImplementedError


class SNSWorkbenchClient(InvestigationProvider):
    def __init__(self, *, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or "https://sns-workbench.example.invalid"
        self.api_key = api_key or "demo-api-key"

    def create_investigation(self, *, context: dict, investigation_id: str):
        return {
            "investigation_id": investigation_id,
            "status": "PENDING",
            "provider": "sns-workbench",
            "asset_id": context["asset"]["id"],
            "alert_id": context["alert"]["id"],
        }


@dataclass
class InvestigationRecord:
    investigation_id: str
    asset_id: int
    alert_id: int
    status: str = "PENDING"
    created_at: datetime = None
    result: XRayInvestigationResult | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class XRayService:
    def __init__(self, provider: InvestigationProvider | None = None):
        self.provider = provider or SNSWorkbenchClient()
        self._records: dict[str, InvestigationRecord] = {}

    def create_investigation(self, *, asset_id: int, alert_id: int) -> XRayInvestigationResult:
        investigation_id = str(uuid4())
        context = InvestigationContextBuilder().build_context(asset_id=asset_id, alert_id=alert_id)
        provider_response = self.provider.create_investigation(context=context.__dict__, investigation_id=investigation_id)

        result = XRayInvestigationResult(
            investigation_id=investigation_id,
            asset_id=asset_id,
            alert_id=alert_id,
            summary=f"{context.asset['asset_code']} investigation initiated.",
            root_cause=context.anomaly["description"],
            confidence="High",
            severity=context.alert["severity"],
            evidence=[Evidence.model_validate(item) for item in context.evidence],
            affected_assets=[relationship["target"] for relationship in context.relationships if relationship.get("target")],
            recommended_actions=[
                "Inspect filters and dampers.",
                "Check airflow path for obstruction.",
                "Inspect upstream equipment if issue persists.",
            ],
            created_at=datetime.now(timezone.utc),
        )

        self._records[investigation_id] = InvestigationRecord(
            investigation_id=investigation_id,
            asset_id=asset_id,
            alert_id=alert_id,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
            result=result,
        )

        return result

    def get_investigation(self, investigation_id: str) -> InvestigationRecord | None:
        return self._records.get(investigation_id)

    def build_status(self, investigation_id: str, status: str = "PENDING") -> dict:
        record = self._records.get(investigation_id)
        if record is None:
            return {"investigation_id": investigation_id, "status": status, "created_at": datetime.now(timezone.utc).isoformat()}
        return {
            "investigation_id": record.investigation_id,
            "asset_id": record.asset_id,
            "alert_id": record.alert_id,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
        }
