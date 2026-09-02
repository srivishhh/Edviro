from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_get_xray_investigation():
    response = client.post("/api/v1/xray/investigations", json={"asset_id": 7, "alert_id": 101})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert payload["investigation_id"]

    investigation_id = payload["investigation_id"]
    result = client.get(f"/api/v1/xray/investigations/{investigation_id}")

    assert result.status_code == 200
    data = result.json()
    assert data["asset_id"] == 7
    assert data["alert_id"] == 101
    assert "root_cause" in data


def test_create_xray_investigation_invalid_asset():
    response = client.post("/api/v1/xray/investigations", json={"asset_id": 999, "alert_id": 101})
    assert response.status_code == 404


def test_create_xray_investigation_invalid_alert():
    response = client.post("/api/v1/xray/investigations", json={"asset_id": 7, "alert_id": 999})
    assert response.status_code == 404
