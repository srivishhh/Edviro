from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class ScenarioConfig:
    name: str
    temperature: tuple[float, float]
    energy: tuple[float, float]
    pressure: tuple[float, float]
    airflow: tuple[float, float]


def get_scenario(name: str) -> ScenarioConfig:
    scenarios = {
        "normal": ScenarioConfig("normal", (22.0, 26.0), (6.0, 9.0), (3.0, 4.0), (90.0, 100.0)),
        "high_energy": ScenarioConfig("high_energy", (24.0, 29.0), (10.0, 14.0), (3.6, 4.4), (85.0, 96.0)),
        "high_temperature": ScenarioConfig("high_temperature", (28.0, 35.0), (8.5, 12.0), (3.8, 4.8), (80.0, 96.0)),
        "airflow_restriction": ScenarioConfig("airflow_restriction", (24.0, 30.0), (7.8, 12.0), (3.4, 4.6), (72.0, 95.0)),
        "pressure_anomaly": ScenarioConfig("pressure_anomaly", (23.0, 28.0), (7.0, 11.0), (4.8, 6.2), (82.0, 98.0)),
        "sensor_failure": ScenarioConfig("sensor_failure", (10.0, 18.0), (1.0, 3.5), (0.5, 1.5), (0.0, 25.0)),
    }
    if name not in scenarios:
        raise ValueError(f"Unknown scenario: {name}")
    return scenarios[name]


def generate_event(scenario_name: str, sequence: int) -> dict:
    cfg = get_scenario(scenario_name)
    base = 0.9 + (sequence % 7) * 0.08
    temperature = round(random.uniform(cfg.temperature[0], cfg.temperature[1]) + (sequence % 3) * 0.35, 2)
    energy = round(random.uniform(cfg.energy[0], cfg.energy[1]) * base, 2)
    pressure = round(random.uniform(cfg.pressure[0], cfg.pressure[1]) + (sequence % 5) * 0.15, 2)
    airflow = round(random.uniform(cfg.airflow[0], cfg.airflow[1]) - (sequence % 4) * 1.2, 2)
    return {
        "event_id": f"sim-{scenario_name}-{sequence:04d}",
        "event_type": "telemetry",
        "asset_id": 7,
        "timestamp": "2026-09-01T00:00:00Z",
        "temperature": temperature,
        "pressure": pressure,
        "airflow": max(0.0, airflow),
        "energy_kw": energy,
    }
