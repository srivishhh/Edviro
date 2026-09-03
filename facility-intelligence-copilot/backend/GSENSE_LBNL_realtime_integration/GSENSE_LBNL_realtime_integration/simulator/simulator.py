from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from confluent_kafka import Producer

from config import get_simulator_config
from scenarios import generate_event


def publish_event(config, scenario: str, sequence: int) -> None:
    event = generate_event(scenario, sequence)
    event["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    producer = Producer({"bootstrap.servers": config.kafka_bootstrap_servers})
    producer.produce(config.telemetry_topic, json.dumps(event).encode("utf-8"))
    producer.flush(timeout=5)
    print(f"Published {event['event_id']} to {config.telemetry_topic}")


def parse_args() -> argparse.Namespace:
    config = get_simulator_config()
    parser = argparse.ArgumentParser(description="Facility telemetry simulator")
    parser.add_argument("--scenario", choices=["normal", "high_energy", "high_temperature", "airflow_restriction", "pressure_anomaly", "sensor_failure"], default="normal")
    parser.add_argument("--interval", type=int, default=config.default_interval_seconds)
    parser.add_argument("--count", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = get_simulator_config()
    for i in range(args.count):
        publish_event(config, args.scenario, i)
        if i < args.count - 1:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
