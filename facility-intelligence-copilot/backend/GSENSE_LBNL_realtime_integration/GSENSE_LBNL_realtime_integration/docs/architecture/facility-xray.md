# Facility X-Ray architecture

## Deterministic analytics

The deterministic pipeline continues to own telemetry validation, threshold evaluation, health scoring, anomaly detection, severity assignment, and alert creation.

Alert
↓
Investigation Context
↓
Digital Twin
↓
Telemetry
↓
SNS Workbench
↓
Root Cause
↓
Evidence
↓
Recommendation

## AI-assisted investigation boundary

Facility X-Ray is intentionally separated from raw threshold logic. The deterministic layer produces evidence and context, while the investigation layer interprets that evidence in support of operations decisions.

This keeps the system auditable and understandable:

- Observed: measured telemetry and sensor values
- Inferred: likely operational cause based on patterns
- Recommended: operator actions based on the observed evidence

## Investigation context

The investigation context combines:

- alert metadata
- current telemetry
- recent telemetry history
- asset metadata
- related equipment and dependencies
- anomaly evidence
- health score and operational state

## Evidence and ranking

The investigation engine ranks evidence by operational importance. In the observed airflow restriction scenario, the ranking is driven by metrics such as:

- airflow below baseline
- temperature rising above baseline
- energy increasing above the normal envelope
- pressure rising while airflow falls
- dependency chain showing related equipment impact

## Hypotheses and confidence

The service model is prepared to hold multiple hypotheses and rank them by evidence, while keeping confidence as a qualified operational signal rather than false precision.

## Future extensibility

The current context model is prepared for future sources such as:

- live telemetry
- historical telemetry
- digital twin state
- maintenance records
- facility documents
- past incidents
- operator notes

No vector database or RAG pipeline is required for the current milestone.

## Trust and safety

The X-Ray output is designed to distinguish between:

- observed measurements
- inferred root-cause hypotheses
- recommended operator actions

This prevents AI reasoning from being presented as sensor truth.

## Current status

- IMPLEMENTED: investigation context, evidence ranking, and structured X-Ray result model
- TESTED: local unit tests for context generation and service behavior
- LIVE VERIFIED: blocked pending actual Kafka/PostgreSQL/SNS infrastructure availability in a runtime host
