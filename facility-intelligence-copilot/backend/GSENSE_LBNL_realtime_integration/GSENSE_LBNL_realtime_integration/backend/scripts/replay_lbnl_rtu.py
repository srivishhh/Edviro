"""Replay real LBNL RTU telemetry into GSENSE as a real-time stream.

The source data is historical experimental data. The script replays it in real time
by assigning each source row a current UTC timestamp while preserving source_timestamp.
The fault ground truth is carried only as an evaluation field; the backend detector
uses telemetry features rather than the label.
"""
from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "lbnl" / "RTU.csv"


def f_to_c(value: float) -> float:
    return (value - 32.0) * 5.0 / 9.0


def row_to_event(row: pd.Series, asset_id: int) -> dict:
    flow = float(row["RTU: Supply Air Volumetric Flow Rate"])
    electricity_wh = float(row["RTU: Electricity"])
    discharge_psi = float(row["RTU: Circuit 1 Discharge Pressure"])
    # Canonical GSENSE units: temperature C, pressure bar, airflow % of ~4400 cfm, energy kW.
    return {
        "event_id": f"lbnl-rtu-{uuid.uuid4().hex[:12]}",
        "event_type": "telemetry",
        "asset_id": asset_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": round(f_to_c(float(row["RTU: Supply Air Temperature"])), 3),
        "pressure": round(discharge_psi * 0.0689475729, 3),
        "airflow": round(min(100.0, max(0.0, flow / 4400.0 * 100.0)), 2),
        "energy_kw": round(electricity_wh * 0.06, 3),
        "source": "LBNL_RTU",
        "source_timestamp": pd.Timestamp(row["Timestamp"]).tz_localize("UTC").isoformat(),
        "fault_ground_truth": int(row["Fault Detection Ground Truth"]),
        "raw_metrics": {
            "supply_air_temperature_f": float(row["RTU: Supply Air Temperature"]),
            "supply_air_flow_cfm": flow,
            "electricity_wh_per_min": electricity_wh,
            "circuit_1_discharge_pressure_psi": discharge_psi,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8000/api/v1/telemetry")
    ap.add_argument("--asset-id", type=int, default=7)
    ap.add_argument("--seconds", type=float, default=1.0)
    ap.add_argument("--rows", type=int, default=120)
    ap.add_argument("--start", default="2017-08-27 06:43")
    args = ap.parse_args()

    df = pd.read_csv(DATA)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    start = pd.Timestamp(args.start)
    df = df[df["Timestamp"] >= start].dropna(subset=[
        "RTU: Supply Air Temperature",
        "RTU: Supply Air Volumetric Flow Rate",
        "RTU: Electricity",
        "RTU: Circuit 1 Discharge Pressure",
    ]).head(args.rows)
    if df.empty:
        raise SystemExit("No complete RTU rows found for the requested start time.")

    print(f"Replaying {len(df)} real LBNL RTU rows to {args.api}")
    for _, row in df.iterrows():
        event = row_to_event(row, args.asset_id)
        r = requests.post(args.api, json=event, timeout=10)
        r.raise_for_status()
        data = r.json()
        print(f"{event['source_timestamp']} -> airflow={event['airflow']}% pressure={event['pressure']}bar energy={event['energy_kw']}kW alerts={len(data.get('alerts', []))}")
        time.sleep(args.seconds)


if __name__ == "__main__":
    main()
