# GSENSE — LBNL real-time telemetry replay

This integration adds the LBNL RTU experimental dataset to GSENSE as a real-time replay.
The source dataset is historical; replay makes it arrive one row at a time as if it were live telemetry.

## Dataset used
`data/lbnl/RTU.csv` contains RTU supply/return air temperatures, fan status, refrigerant pressures/temperatures, volumetric airflow, electricity, natural gas, occupancy, room conditions and a fault ground-truth label. The included LBNL inventory describes a condenser-fouling fault scenario.

## Run
From `backend`:

```powershell
pip install -r requirements.txt
python scripts/replay_lbnl_rtu.py --asset-id 7 --seconds 1 --rows 120
```

Keep FastAPI running on `127.0.0.1:8000`. Open GSENSE asset **HVAC-007**. The Asset Details page polls every 2 seconds, so the chart/metrics update while the replay is running.

## Data mapping
- supply air temperature °F → °C
- circuit 1 discharge pressure psi → bar
- supply air volumetric flow cfm → airflow index (%) relative to 4400 cfm
- electricity Wh/min → kW
- original timestamp → `source_timestamp`
- LBNL fault label → `fault_ground_truth` (evaluation only)

The detector does not use `fault_ground_truth` to create alerts. For LBNL RTU replay, elevated discharge pressure plus electrical demand can generate `CONDENSER_FOULING`.

## Demo
1. Start PostgreSQL/backend.
2. Open GSENSE → Assets → HVAC-007.
3. Start the replay.
4. Watch the latest telemetry change.
5. When the feature-based detector sees the condenser-fouling pattern, an alert is created.
6. Use Facility X-Ray/SNS Workbench to investigate the alert.

If Kafka is running, the same normalized event can later be published to the telemetry Kafka topic instead of using HTTP replay.
