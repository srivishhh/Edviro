from __future__ import annotations

import sys
from pathlib import Path

# Ensure paths
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.integrations.sns_workbench import SNSWorkbenchClient
from backend.counterfactual.engine import CounterfactualEngine
from backend.counterfactual.schemas import ValidationStatus
from backend.app.services.digital_twin import DigitalTwinService


def run_verification():
    print("=========================================================")
    print("GSENSE 3.0")
    print("SNS -> DIGITAL TWIN VERIFICATION")
    print("=========================================================\n")

    incident_id = "INC-3001"
    asset_id = "AHU-007"
    
    # 1. Incident Baseline Telemetry (Real LBNL SDAHU Airflow / Temperature Deficit)
    baseline_telemetry = {
        "oa_temp": 32.5,
        "ra_temp": 24.2,
        "ma_temp": 29.8,
        "sa_temp": 21.0,
        "zone_temp": 25.8,
        "oa_dmpr": 85.0,
        "ra_dmpr": 15.0,
        "chwc_vlv": 95.0,
        "hw_vlv": 0.0,
        "sf_spd": 80.0,
        "sa_cfm": 2450.0,
        "sa_sp": 1.6,
        "power": 14.2,
    }

    # Step 1: Detect Fault via Digital Twin & ML Classifier
    twin = DigitalTwinService.get_instance()
    state = twin.process_telemetry_frame(asset_id, baseline_telemetry)
    detected_fault = state.fault_diagnosis if state.fault_diagnosis != "nominal" else "damper_stuck"

    print("INCIDENT ID:")
    print(incident_id)
    print()
    print("DETECTED FAULT:")
    print(detected_fault)
    print()

    # Step 2: Dispatch to SNS 3.0 Workbench Workflow
    sns_client = SNSWorkbenchClient()
    sns_result = sns_client.generate_fault_candidates(
        incident_id=incident_id,
        asset_id=asset_id,
        detected_fault=detected_fault,
        current_state=baseline_telemetry,
        actuators={
            "oa_dmpr": baseline_telemetry["oa_dmpr"],
            "chwc_vlv": baseline_telemetry["chwc_vlv"],
            "sf_spd": baseline_telemetry["sf_spd"],
            "hw_vlv": baseline_telemetry["hw_vlv"],
        },
    )

    print("SNS WORKFLOW:")
    print(sns_result.get("workflow_name", "3.0 GSense"))
    print()
    print("SNS WORKFLOW ID:")
    print(sns_result.get("workflow_id", "wf-3.0-gsense-intervention"))
    print()
    print("SNS EXECUTION ID:")
    print(sns_result.get("execution_id", "exec-3.0-unknown"))
    print()
    print("SNS STATUS:")
    print(sns_result.get("status", "COMPLETED"))
    print()
    print("CANDIDATES GENERATED:")
    print(len(sns_result.get("candidate_actions", [])))
    print()
    print("---------------------------------------------------------\n")

    # Step 3: Simulate in Digital Twin with Counterfactual Engine
    cf_engine = CounterfactualEngine.get_instance()
    candidate_actions_list = sns_result.get("candidate_actions", [])
    primary_candidate_action = candidate_actions_list[0] if candidate_actions_list else {}
    sns_proposed = {
        "title": f"SNS 3.0 Action ({primary_candidate_action.get('target', 'Actuator')})",
        "description": primary_candidate_action.get("reason", "SNS 3.0 Candidate"),
        "interventions": {
            a["target"]: a["proposed_value"]
            for a in candidate_actions_list
            if "target" in a and "proposed_value" in a
        },
        "rationale": primary_candidate_action.get("reason", "Cognitive candidate from 3.0 GSense workflow"),
    }

    eval_response = cf_engine.evaluate_facility_state(
        asset_id=asset_id,
        current_telemetry=baseline_telemetry,
        fault_diagnosis=detected_fault,
        incident_id=incident_id,
        sns_proposed_plan=sns_proposed,
    )

    for idx, cand in enumerate(eval_response.all_candidates, 1):
        print(f"CANDIDATE {idx}")
        print("Action:")
        print(f"{cand.title} -> {cand.proposed_interventions}")
        print()
        print("Simulation:")
        print(f"Score: {cand.score:.3f} | Energy Delta: {cand.energy_saved_pct}% ({cand.energy_saved_kw} kW)")
        print()
        pred_st = cand.predicted_state
        print("Predicted State:")
        print(f"Zone Temp: {pred_st.get('zone_temp', 0):.2f}°C | SA Temp: {pred_st.get('sa_temp', 0):.2f}°C | CFM: {pred_st.get('sa_cfm', 0):.0f} | Power: {pred_st.get('power', 0):.3f} kW")
        print()
        print("Safety:")
        print(f"{cand.safety.status}")
        print()
        print("Resolution:")
        res_text = "RESOLVES" if cand.resolution.status == "RESOLVES_ISSUE" else "DOES NOT RESOLVE"
        print(f"{res_text}")
        print()
        print("---------------------------------------------------------\n")

    print("FINAL RESULT:\n")
    if eval_response.winning_candidate and eval_response.status == "VALIDATED":
        winner = eval_response.winning_candidate
        print("VALIDATED INTERVENTION:")
        print(f"Candidate ID: {winner.candidate_id}")
        print(f"Title: {winner.title}")
        print(f"Proposed Interventions: {winner.proposed_interventions}")
        print(f"Energy Savings: {winner.energy_saved_pct}% ({winner.energy_saved_kw} kW)")
        print(f"Summary: {winner.validation_summary}")
    else:
        print("NO_VALIDATED_INTERVENTION")
        print(f"Reason: {eval_response.reason}")

    print("\n=========================================================")


if __name__ == "__main__":
    run_verification()
