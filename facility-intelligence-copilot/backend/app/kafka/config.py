from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KafkaConfig:
    bootstrap_servers: str = "localhost:9092"
    client_id: str = "facility-intelligence-copilot"
    security_protocol: str = "PLAINTEXT"


def get_kafka_config() -> KafkaConfig:
    import os

    return KafkaConfig(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        client_id=os.getenv("KAFKA_CLIENT_ID", "facility-intelligence-copilot"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
    )
