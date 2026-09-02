from app.xray.investigation import InvestigationContextBuilder


def test_xray_context_includes_alert_and_telemetry():
    builder = InvestigationContextBuilder()
    context = builder.build_context(asset_id=7, alert_id=101)

    assert context.asset["asset_code"] == "HVAC-007"
    assert context.alert["alert_type"] == "AIRFLOW_RESTRICTION"
    assert context.current_state["airflow"] == 64.0
    assert context.recent_history[0]["airflow"] == 72.0
    assert context.relationships[0]["target"] == "Floor 2"
    assert context.anomaly["type"] == "AIRFLOW_RESTRICTION"
    assert context.evidence[0]["metric"] == "airflow"
