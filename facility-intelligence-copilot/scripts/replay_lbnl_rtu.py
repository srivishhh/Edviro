#!/usr/bin/env python3
"""
GSENSE — LBNL RTU Real-Time Telemetry Replay Engine
===================================================
Replays real historical commercial HVAC Rooftop Unit (RTU) telemetry from Lawrence
Berkeley National Laboratory (LBNL) into GSENSE Facility Intelligence Copilot.

Usage:
    python scripts/replay_lbnl_rtu.py --asset-id 7 --seconds 1 --rows 120
    python scripts/replay_lbnl_rtu.py --asset-id 7 --interval 0.5 --start-row 400
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("lbnl_replay")

# Default settings
DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_ASSET_ID = 7  # HVAC-007
DEFAULT_INTERVAL_SECONDS = 1.0
DEFAULT_START_ROW = 400  # Row where compressor 1 & airflow measurements are active
RATED_CFM = 4500.0  # Nominal rated volumetric airflow for commercial RTU


def find_csv_path() -> Path:
    """Finds the LBNL RTU.csv dataset across standard project paths."""
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "lbnl" / "RTU.csv",
        Path(__file__).resolve().parent / "data" / "lbnl" / "RTU.csv",
        Path.cwd() / "backend" / "data" / "lbnl" / "RTU.csv",
        Path.cwd() / "data" / "lbnl" / "RTU.csv",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "Could not locate RTU.csv. Ensure backend/data/lbnl/RTU.csv exists."
    )


def parse_float_safe(val: str | None, default: float = 0.0) -> float:
    """Safely converts string or NA to float."""
    if not val or val.strip().upper() in ("NA", "NAN", "NULL", ""):
        return default
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return default


def fahrenheit_to_celsius(f: float) -> float:
    """Converts Fahrenheit to Celsius."""
    return (f - 32.0) * (5.0 / 9.0)


def psi_to_bar(psi: float) -> float:
    """Converts PSI to Bar."""
    return psi * 0.0689476


def transform_lbnl_row(row: dict[str, str], row_idx: int, asset_id: int) -> dict[str, Any]:
    """
    Transforms a single raw LBNL RTU row into a normalized GSENSE TelemetryEvent payload.
    """
    raw_timestamp = row.get("Timestamp", "")
    
    try:
        dt = datetime.strptime(raw_timestamp, "%m/%d/%Y %H:%M")
        iso_timestamp = dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        iso_timestamp = datetime.now(timezone.utc).isoformat()

    supply_temp_f = parse_float_safe(row.get("RTU: Supply Air Temperature"), 68.0)
    supply_temp_c = round(fahrenheit_to_celsius(supply_temp_f), 2)
    
    return_temp_f = parse_float_safe(row.get("RTU: Return Air Temperature"), 72.0)
    return_temp_c = round(fahrenheit_to_celsius(return_temp_f), 2)

    cond_temp_f = parse_float_safe(row.get("RTU: Circuit 1 Condenser Outlet Temperature"), 85.0)
    cond_temp_c = round(fahrenheit_to_celsius(cond_temp_f), 2)

    disch_press_psi = parse_float_safe(row.get("RTU: Circuit 1 Discharge Pressure"), 180.0)
    disch_press_bar = round(psi_to_bar(disch_press_psi), 2) if disch_press_psi > 0 else 3.8

    flow_cfm = parse_float_safe(row.get("RTU: Supply Air Volumetric Flow Rate"), 4200.0)
    airflow_pct = round(min(100.0, max(0.0, (flow_cfm / RATED_CFM) * 100.0)), 1)

    raw_electricity = parse_float_safe(row.get("RTU: Electricity"), 8.5)
    energy_kw = round(max(1.0, min(250.0, raw_electricity)), 2)

    fan_status = int(parse_float_safe(row.get("RTU: Supply Air Fan Status"), 1.0))
    comp1_status = int(parse_float_safe(row.get("RTU: Compressor 1 On/Off Status"), 1.0))
    occupancy = int(parse_float_safe(row.get("Occupancy Mode Indicator"), 1.0))

    event_id = f"lbnl-evt-{row_idx:06d}-{int(time.time() * 1000) % 1000000}"

    return {
        "event_id": event_id,
        "event_type": "telemetry",
        "asset_id": asset_id,
        "timestamp": iso_timestamp,
        "temperature": supply_temp_c,
        "pressure": disch_press_bar,
        "airflow": airflow_pct,
        "energy_kw": energy_kw,
        "raw_data": {
            "source": "LBNL_RTU_HISTORICAL_REPLAY",
            "dataset_row": row_idx,
            "original_timestamp": raw_timestamp,
            "supply_air_temp_f": supply_temp_f,
            "return_air_temp_c": return_temp_c,
            "condenser_temp_c": cond_temp_c,
            "discharge_pressure_psi": disch_press_psi,
            "flow_cfm": flow_cfm,
            "fan_status": fan_status,
            "compressor_status": comp1_status,
            "occupancy": occupancy,
        },
    }


def send_telemetry_http(payload: dict[str, Any], api_url: str) -> dict[str, Any]:
    """Dispatches a single telemetry payload to FastAPI ingestion endpoint."""
    url = f"{api_url.rstrip('/')}/api/v1/telemetry"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5.0) as response:
        res_bytes = response.read()
        return json.loads(res_bytes.decode("utf-8"))


class ReplayRunner:
    def __init__(
        self,
        csv_path: Path,
        asset_id: int = DEFAULT_ASSET_ID,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        start_row: int = DEFAULT_START_ROW,
        max_rows: int | None = None,
        api_url: str = DEFAULT_API_URL,
    ):
        self.csv_path = csv_path
        self.asset_id = asset_id
        self.interval = interval_seconds
        self.start_row = start_row
        self.max_rows = max_rows
        self.api_url = api_url
        self.running = True
        self.replayed_count = 0
        self.detected_alerts_count = 0

    def handle_signal(self, signum: int, frame: Any) -> None:
        logger.info("\n[LBNL REPLAY] Shutdown signal received. Gracefully stopping replay...")
        self.running = False

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        logger.info("=" * 70)
        logger.info("  GSENSE — LBNL RTU Real-Time Telemetry Replay Engine")
        logger.info("=" * 70)
        logger.info(f"Dataset File      : {self.csv_path}")
        logger.info(f"Target Asset ID   : {self.asset_id} (HVAC-007)")
        logger.info(f"Replay Interval   : {self.interval}s per record")
        logger.info(f"Start Row Offset  : {self.start_row}")
        logger.info(f"Max Rows Limit    : {self.max_rows or 'ALL (30,240)'}")
        logger.info(f"Ingestion API     : {self.api_url}/api/v1/telemetry")
        logger.info("-" * 70)
        logger.info("Starting real-time sequential stream... (Press Ctrl+C to stop)\n")

        start_time = time.time()

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader, start=1):
                if not self.running:
                    break
                if row_idx < self.start_row:
                    continue
                if self.max_rows is not None and self.replayed_count >= self.max_rows:
                    logger.info(f"[LBNL REPLAY] Target row limit reached ({self.max_rows} rows).")
                    break

                payload = transform_lbnl_row(row, row_idx, self.asset_id)

                try:
                    response = send_telemetry_http(payload, self.api_url)
                    self.replayed_count += 1

                    raw = payload["raw_data"]
                    logger.info(
                        f"[LBNL REPLAY] row: {row_idx:05d} | "
                        f"time: {payload['timestamp']} | "
                        f"asset: HVAC-{self.asset_id:03d} | "
                        f"temp: {payload['temperature']:5.1f}°C ({raw['supply_air_temp_f']:5.1f}°F) | "
                        f"press: {payload['pressure']:5.1f} bar ({raw['discharge_pressure_psi']:5.1f} psi) | "
                        f"flow: {payload['airflow']:5.1f}% ({raw['flow_cfm']:4.0f} CFM) | "
                        f"power: {payload['energy_kw']:6.2f} kW"
                    )

                    alerts = response.get("alerts", [])
                    anomalies = response.get("anomalies", [])
                    
                    if alerts:
                        for alt in alerts:
                            self.detected_alerts_count += 1
                            logger.warning(
                                f"  ↳ [ALERT] alert_id: {alt.get('id', 'N/A')} | "
                                f"type: {alt.get('alert_type')} | "
                                f"severity: {alt.get('severity')} | "
                                f"score: {alt.get('anomaly_score')} | "
                                f"msg: {alt.get('message')}"
                            )
                    elif anomalies:
                        for anom in anomalies:
                            logger.warning(
                                f"  ↳ [ANOMALY DETECTOR] type: {anom.get('alert_type')} | "
                                f"score: {anom.get('anomaly_score')} | "
                                f"reason: {anom.get('message')}"
                            )

                except urllib.error.URLError as err:
                    logger.error(
                        f"[LBNL REPLAY] Transmission error on row {row_idx}: {err}. Retrying next interval..."
                    )
                except Exception as exc:
                    logger.error(f"[LBNL REPLAY] Unexpected error processing row {row_idx}: {exc}")

                time.sleep(self.interval)

        elapsed = round(time.time() - start_time, 2)
        logger.info("\n" + "=" * 70)
        logger.info("  LBNL Replay Summary Report")
        logger.info("=" * 70)
        logger.info(f"Total Rows Emitted   : {self.replayed_count}")
        logger.info(f"Alerts Triggered     : {self.detected_alerts_count}")
        logger.info(f"Total Elapsed Time   : {elapsed} seconds")
        logger.info("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GSENSE — LBNL RTU Real-Time Telemetry Replay Script"
    )
    parser.add_argument(
        "--asset-id",
        type=int,
        default=DEFAULT_ASSET_ID,
        help="Target GSENSE Asset ID (default: 7 for HVAC-007)",
    )
    parser.add_argument(
        "--seconds",
        "--interval",
        dest="interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Streaming interval in seconds between records (default: 1.0)",
    )
    parser.add_argument(
        "--rows",
        "--limit",
        dest="rows",
        type=int,
        default=None,
        help="Maximum rows to replay (default: full dataset)",
    )
    parser.add_argument(
        "--start-row",
        "--offset",
        dest="start_row",
        type=int,
        default=DEFAULT_START_ROW,
        help="Starting CSV row index (default: 400 where compressor is active)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"FastAPI backend base URL (default: {DEFAULT_API_URL})",
    )

    args = parser.parse_args()

    try:
        csv_path = find_csv_path()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    runner = ReplayRunner(
        csv_path=csv_path,
        asset_id=args.asset_id,
        interval_seconds=args.interval,
        start_row=args.start_row,
        max_rows=args.rows,
        api_url=args.api_url,
    )
    runner.run()


if __name__ == "__main__":
    main()
