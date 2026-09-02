from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SimulatorConfig:
    kafka_bootstrap_servers: str = "localhost:9092"
    telemetry_topic: str = "facility.telemetry"
    asset_id: int = 7
    default_interval_seconds: int = 5


def get_simulator_config() -> SimulatorConfig:
    return SimulatorConfig(
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        telemetry_topic=os.getenv("KAFKA_TELEMETRY_TOPIC", "facility.telemetry"),
        asset_id=int(os.getenv("SIMULATOR_ASSET_ID", "7")),
        default_interval_seconds=int(os.getenv("SIMULATION_INTERVAL_SECONDS", "5")),
    )
