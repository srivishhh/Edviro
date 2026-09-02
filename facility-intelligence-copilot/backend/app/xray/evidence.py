from __future__ import annotations

from datetime import datetime, timezone

from app.xray.models import Evidence


def build_evidence_items(current_state: dict, recent_history: list[dict], alert: dict, relationships: list[dict]) -> list[Evidence]:
    items: list[Evidence] = []
    baseline = recent_history[0] if recent_history else {}

    if current_state.get("airflow") is not None:
        base_val = float(baseline.get("airflow", 95.0))
        cur_val = float(current_state["airflow"])
        items.append(
            Evidence(
                source="sensor",
                metric="airflow",
                value=cur_val,
                current_value=cur_val,
                baseline=base_val,
                expected_range="90-100%",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Airflow is significantly below the expected operating range.",
                importance=0.95,
            )
        )
    if current_state.get("temperature") is not None:
        base_val = float(baseline.get("temperature", 23.0))
        cur_val = float(current_state["temperature"])
        items.append(
            Evidence(
                source="sensor",
                metric="temperature",
                value=cur_val,
                current_value=cur_val,
                baseline=base_val,
                expected_range="20-26°C",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Temperature is elevated relative to the normal operating envelope.",
                importance=0.85,
            )
        )
    if current_state.get("energy_kw") is not None:
        base_val = float(baseline.get("energy_kw", 5.5))
        cur_val = float(current_state["energy_kw"])
        items.append(
            Evidence(
                source="sensor",
                metric="energy",
                value=cur_val,
                current_value=cur_val,
                baseline=base_val,
                expected_range="5-8 kW",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Energy draw is elevated and consistent with reduced airflow efficiency.",
                importance=0.80,
            )
        )
    if current_state.get("pressure") is not None:
        base_val = float(baseline.get("pressure", 3.8))
        cur_val = float(current_state["pressure"])
        items.append(
            Evidence(
                source="sensor",
                metric="pressure",
                value=cur_val,
                current_value=cur_val,
                baseline=base_val,
                expected_range="3.0-4.0 bar",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Pressure increased while airflow dropped, consistent with a restriction in the path.",
                importance=0.90,
            )
        )
    if alert:
        score = float(alert.get("anomaly_score", 0.0))
        items.append(
            Evidence(
                source="alert",
                metric="anomaly_score",
                value=score,
                current_value=score,
                baseline=0.0,
                expected_range="0.0-0.5",
                timestamp=alert.get("detected_at") or datetime.now(timezone.utc),
                interpretation=f"Alert type {alert.get('alert_type')} is active and matches the observed operating pattern.",
                importance=0.88,
            )
        )
    if relationships:
        items.append(
            Evidence(
                source="digital_twin",
                metric="related_assets",
                value=", ".join(rel.get("target", "") for rel in relationships[:3] if rel.get("target")),
                current_value=len(relationships),
                baseline=0,
                expected_range="upstream/downstream dependencies",
                timestamp=datetime.now(timezone.utc),
                interpretation="The affected asset has a direct dependency chain that suggests the issue is local to the airflow path and upstream support equipment.",
                importance=0.75,
            )
        )
    if recent_history:
        baseline_airflow = baseline.get("airflow")
        if baseline_airflow is not None and current_state.get("airflow") is not None:
            delta = float(current_state["airflow"] - baseline_airflow)
            items.append(
                Evidence(
                    source="historical_telemetry",
                    metric="baseline_airflow_delta",
                    value=delta,
                    current_value=delta,
                    baseline=0.0,
                    expected_range="-5 to +5%",
                    timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                    interpretation="Current airflow is materially below the recent baseline for this asset.",
                    importance=0.92,
                )
            )
    return items

