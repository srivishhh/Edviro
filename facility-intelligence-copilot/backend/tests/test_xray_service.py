from app.xray.service import XRayService


class MockProvider:
    def __init__(self):
        self.calls = []

    def create_investigation(self, *, context, investigation_id):
        self.calls.append({"context": context, "investigation_id": investigation_id})
        return {
            "investigation_id": investigation_id,
            "asset_id": context["asset"]["id"],
            "alert_id": context["alert"]["id"],
            "summary": "Airflow restriction confirmed.",
            "root_cause": "Airflow restriction in HVAC-007.",
            "confidence": "High",
            "severity": "WARNING",
            "evidence": [{
                "source": "sensor",
                "metric": "airflow",
                "value": 72,
                "expected_range": "90-100%",
                "timestamp": "2026-09-01T12:15:00Z",
                "interpretation": "Airflow is below the expected operating range.",
            }],
            "affected_assets": ["CHILLER-002", "Floor 2"],
            "recommended_actions": [
                "Inspect filters and dampers.",
                "Check upstream airflow path.",
            ],
        }


def test_xray_service_creates_investigation():
    provider = MockProvider()
    service = XRayService(provider=provider)

    result = service.create_investigation(asset_id=7, alert_id=101)

    assert result.investigation_id
    assert result.asset_id == 7
    assert result.alert_id == 101
    assert result.root_cause.startswith("Airflow")
    assert provider.calls
