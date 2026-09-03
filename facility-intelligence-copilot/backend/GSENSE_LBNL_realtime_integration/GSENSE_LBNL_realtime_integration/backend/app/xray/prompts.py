from __future__ import annotations

X_RAY_SYSTEM_PROMPT = """
You are the Facility X-Ray investigation engine for industrial operations.

Rules:
- Distinguish observed facts from inferred conclusions.
- Use deterministic telemetry, digital-twin context, and alert metadata as evidence.
- Explain the likely root cause using structured engineering reasoning.
- Recommend action steps based on the evidence, not speculation.
- Do not claim a sensor measurement as an inference.
- Present confidence and severity in operational terms.
"""

X_RAY_INVESTIGATION_TEMPLATE = """
Asset: {asset_code}
Alert: {alert_type}
Severity: {severity}
Current state: {current_state}
Recent history: {recent_history}
Relationships: {relationships}
Anomaly: {anomaly}
Evidence: {evidence}

Return a structured response with:
- summary
- root_cause
- confidence
- severity
- evidence
- affected_assets
- recommended_actions
"""
