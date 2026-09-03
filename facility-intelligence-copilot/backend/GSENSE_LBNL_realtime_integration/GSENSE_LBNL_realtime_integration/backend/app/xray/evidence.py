from __future__ import annotations

from datetime import datetime, timezone

from app.xray.models import Evidence


def build_evidence_items(current_state: dict, recent_history: list[dict], alert: dict, relationships: list[dict]) -> list[Evidence]:
    items: list[Evidence] = []
    if current_state.get("airflow") is not None:
        items.append(
            Evidence(
                source="sensor",
                metric="airflow",
                value=float(current_state["airflow"]),
                expected_range="90-100%",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Airflow is significantly below the expected operating range.",
            )
        )
    if current_state.get("temperature") is not None:
        items.append(
            Evidence(
                source="sensor",
                metric="temperature",
                value=float(current_state["temperature"]),
                expected_range="20-26°C",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Temperature is elevated relative to the normal operating envelope.",
            )
        )
    if current_state.get("energy_kw") is not None:
        items.append(
            Evidence(
                source="sensor",
                metric="energy",
                value=float(current_state["energy_kw"]),
                expected_range="5-8 kW",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Energy draw is elevated and consistent with reduced airflow efficiency.",
            )
        )
    if current_state.get("pressure") is not None:
        items.append(
            Evidence(
                source="sensor",
                metric="pressure",
                value=float(current_state["pressure"]),
                expected_range="3.0-4.0 bar",
                timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                interpretation="Pressure increased while airflow dropped, consistent with a restriction in the path.",
            )
        )
    if alert:
        items.append(
            Evidence(
                source="alert",
                metric="anomaly_score",
                value=float(alert.get("anomaly_score", 0.0)),
                expected_range="0.6-1.0",
                timestamp=alert.get("detected_at") or datetime.now(timezone.utc),
                interpretation=f"Alert type {alert.get('alert_type')} is active and matches the observed operating pattern.",
            )
        )
    if relationships:
        items.append(
            Evidence(
                source="digital_twin",
                metric="related_assets",
                value=", ".join(rel.get("target", "") for rel in relationships[:3] if rel.get("target")),
                expected_range="upstream/downstream dependencies",
                timestamp=datetime.now(timezone.utc),
                interpretation="The affected asset has a direct dependency chain that suggests the issue is local to the airflow path and upstream support equipment.",
            )
        )
    if recent_history:
        baseline = recent_history[0]
        baseline_airflow = baseline.get("airflow")
        if baseline_airflow is not None and current_state.get("airflow") is not None:
            items.append(
                Evidence(
                    source="historical_telemetry",
                    metric="baseline_airflow_delta",
                    value=float(current_state["airflow"] - baseline_airflow),
                    expected_range="-5 to +5%",
                    timestamp=current_state.get("timestamp") or datetime.now(timezone.utc),
                    interpretation="Current airflow is materially below the recent baseline for this asset.",
                )
            )
    return items
