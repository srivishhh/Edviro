from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_xray_investigation_works_without_live_database():
    response = client.post("/api/v1/xray/investigations", json={"asset_id": 7, "alert_id": 101})

    assert response.status_code == 202
    payload = response.json()
    assert payload["asset_id"] == 7
    assert payload["alert_id"] == 101
    assert payload["status"] == "PENDING"
    assert payload["summary"]
