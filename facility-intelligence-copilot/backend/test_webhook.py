import os
import json
from dotenv import load_dotenv
from app.integrations.sns_workbench import SNSWorkbenchClient

load_dotenv()

client = SNSWorkbenchClient()

test_payload = {
    "event_type": "asset_anomaly",
    "facility_id": "FAC-001",
    "building_id": "BLDG-A",
    "asset_id": "7",
    "telemetry": {},
    "digital_twin": {},
    "alerts": [],
    "anomalies": []
}

print(f"Webhook URL configured: {client.webhook_url}")
response = client.send_facility_event(test_payload)
print(json.dumps(response, indent=2))
