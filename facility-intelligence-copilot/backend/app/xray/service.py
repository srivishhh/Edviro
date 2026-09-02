from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.xray.investigation import InvestigationContextBuilder
from app.xray.models import Evidence, XRayInvestigationResult
from app.integrations.sns_workbench import SNSWorkbenchClient

_client = SNSWorkbenchClient()

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
    def __init__(self, provider=None):
        self.provider = provider or _client
        self._records: dict[str, InvestigationRecord] = {}

    def create_investigation(self, *, asset_id: int, alert_id: int) -> XRayInvestigationResult:
        investigation_id = str(uuid4())
        context = InvestigationContextBuilder().build_context(asset_id=asset_id, alert_id=alert_id)
        
        # Build SNS event contract
        sns_event = {
            "event_type": "asset_anomaly",
            "facility_id": "FAC-001",
            "building_id": "BLDG-A",
            "floor_id": "F2",
            "zone_id": "ZONE-2B",
            "asset_id": str(asset_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "telemetry": context.telemetry if hasattr(context, 'telemetry') else {},
            "digital_twin": {
                "asset": context.asset,
                "relationships": context.relationships
            },
            "investigation_id": investigation_id,
            "event_id": str(alert_id),
            "alert_context": context.alert,
        }
        
        # Make the request to SNS Workbench
        try:
            sns_res = self.provider.send_facility_event(sns_event)
        except Exception:
            sns_res = {}
            
        validated_result = None
        try:
            validated_result = XRayInvestigationResult.model_validate(sns_res)
        except Exception as e:
            # Fallback if invalid or empty
            print(f"Failed to validate response: {e}")
            validated_result = XRayInvestigationResult(
                investigation_id=investigation_id,
                event_id=str(alert_id),
                status="FAILED",
                event_class="UNKNOWN",
                incident_assurance={
                    "decision": "REQUIRES_REVIEW",
                    "confidence": 0.0,
                    "notification_allowed": False
                }
            )

        self._records[investigation_id] = InvestigationRecord(
            investigation_id=investigation_id,
            asset_id=asset_id,
            alert_id=alert_id,
            status=validated_result.status,
            created_at=datetime.now(timezone.utc),
            result=validated_result,
        )

        return validated_result

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
