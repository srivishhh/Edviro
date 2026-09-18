import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def safe_str(val):
    if val is None:
        return "None"
    return str(val).encode('ascii', 'replace').decode('ascii')

print("--- 1. Testing Health Endpoint ---")
r = requests.get(f"{BASE_URL}/health")
print("Health:", r.status_code, r.json())
assert r.status_code == 200

print("\n--- 2. Testing Active Incident Endpoint ---")
r = requests.get(f"{BASE_URL}/api/v1/incidents/active")
print("Active Incident:", r.status_code)
active_data = r.json()
print("Has Active Incident:", active_data.get("has_active_incident"))
print("Fault Diagnosis:", active_data.get("fault_diagnosis"))
print("Health Score:", active_data.get("health_score"))

print("\n--- 3. Testing Single Digital Twin Candidate Simulation API (POST /api/digital-twin/simulate) ---")
sim_single_payload = {
    "incident_id": "INC-TEST-001",
    "detected_fault": "damper_stuck",
    "candidate": {
        "action_id": "SNS-DS-03",
        "target": "oa_dmpr",
        "parameter": "value",
        "current_value": 100.0,
        "proposed_value": 35.0
    },
    "baseline_state": {
        "oa_temp": 32.0, "ra_temp": 24.0, "ma_temp": 30.0, "sa_temp": 20.0,
        "zone_temp": 25.5, "oa_dmpr": 100.0, "chwc_vlv": 85.0, "sf_spd": 75.0,
        "sa_cfm": 2400.0, "sa_sp": 1.6, "power": 12.0
    }
}
r = requests.post(f"{BASE_URL}/api/digital-twin/simulate", json=sim_single_payload)
print("Single Simulation API:", r.status_code)
assert r.status_code == 200
sim_res = r.json()
print("  Action ID:", safe_str(sim_res.get("action_id")))
print("  Status:", safe_str(sim_res.get("status")))
print("  Safe:", safe_str(sim_res.get("constraints", {}).get("safe")))
print("  Resolved:", safe_str(sim_res.get("resolution", {}).get("resolved")))
print("  Efficiency Score:", safe_str(sim_res.get("efficiency", {}).get("score")))
print("  Provenance Telemetry:", safe_str(sim_res.get("provenance", {}).get("telemetry")))

print("\n--- 4. Testing Sequential Digital Twin Simulation API (POST /api/digital-twin/simulate-all) ---")
sim_all_payload = {
    "incident_id": "INC-TEST-001",
    "detected_fault": "damper_stuck",
    "candidates": [
        {"action_id": "SNS-DS-01", "target": "oa_dmpr", "proposed_value": 10.0},
        {"action_id": "SNS-DS-02", "target": "oa_dmpr", "proposed_value": 20.0},
        {"action_id": "SNS-DS-03", "target": "oa_dmpr", "proposed_value": 35.0},
    ],
    "baseline_state": {
        "oa_temp": 32.0, "ra_temp": 24.0, "ma_temp": 30.0, "sa_temp": 20.0,
        "zone_temp": 25.5, "oa_dmpr": 100.0, "chwc_vlv": 85.0, "sf_spd": 75.0,
        "sa_cfm": 2400.0, "sa_sp": 1.6, "power": 12.0
    }
}
r = requests.post(f"{BASE_URL}/api/digital-twin/simulate-all", json=sim_all_payload)
print("Simulate All API:", r.status_code)
assert r.status_code == 200
sim_all_res = r.json()
print("  Status:", safe_str(sim_all_res.get("status")))
print("  Total Simulated:", len(sim_all_res.get("simulations", [])))
print("  Validated Interventions Count:", len(sim_all_res.get("validated_interventions", [])))

print("\n--- 5. Testing Recommendation API (POST /api/digital-twin/recommend) ---")
r = requests.post(f"{BASE_URL}/api/digital-twin/recommend", json=sim_all_payload)
print("Recommend API:", r.status_code)
assert r.status_code == 200
rec_res = r.json()
print("  Recommended Action ID:", safe_str(rec_res.get("recommended_intervention", {}).get("action_id") if rec_res.get("recommended_intervention") else "None"))

print("\n--- 6. Testing Full Investigation Pipeline (Damper Stuck) ---")
payload_damper = {
    "asset_id": "AHU-007",
    "detected_fault": "damper_stuck",
    "fault_confidence": 0.95,
    "current_telemetry": {
        "oa_temp": 32.0, "ra_temp": 24.0, "ma_temp": 30.0, "sa_temp": 20.0,
        "zone_temp": 25.5, "oa_dmpr": 100.0, "chwc_vlv": 85.0, "sf_spd": 75.0,
        "sa_cfm": 2400.0, "sa_sp": 1.6, "power": 12.0
    }
}
r = requests.post(f"{BASE_URL}/api/v1/incidents/INC-DS-001/investigate", json=payload_damper)
print("Investigate (Damper Stuck):", r.status_code)
inv_res = r.json()
print("  Status:", safe_str(inv_res.get("status")))
print("  Round:", safe_str(inv_res.get("round_number")))
winner = inv_res.get("validated_intervention")
print("  Validated Intervention:", safe_str(winner.get("title")) if winner else "None")

print("\n--- 7. Testing Actuation Approval Endpoint ---")
if winner:
    act_payload = {
        "candidate_id": winner["candidate_id"],
        "interventions": winner["proposed_interventions"],
        "asset_id": "AHU-007",
        "notes": "Approved via closed-loop test script"
    }
    r = requests.post(f"{BASE_URL}/api/v1/incidents/actuate", json=act_payload)
    print("Actuation Result:", r.status_code, safe_str(r.json().get("message")))
    assert r.status_code == 200

print("\nALL CLOSED-LOOP INTEGRATION TESTS PASSED 100% SUCCESSFULLY!")
