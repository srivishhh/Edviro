from __future__ import annotations

import json

from app.kafka.config import get_kafka_config
from app.kafka.topics import TOPIC_TELEMETRY
from app.schemas.telemetry import TelemetryEvent

try:
    from confluent_kafka import Producer
except ImportError:  # pragma: no cover
    Producer = None


class KafkaProducerClient:
    def __init__(self, bootstrap_servers: str | None = None):
        self.config = get_kafka_config()
        self.bootstrap_servers = bootstrap_servers or self.config.bootstrap_servers
        self._producer = None

        if Producer is not None:
            self._producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": self.config.client_id,
                "security.protocol": self.config.security_protocol,
            })

    def produce(self, topic: str, payload: dict) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer is unavailable because confluent-kafka is not installed.")

        serialized = json.dumps(payload).encode("utf-8")
        self._producer.produce(topic, value=serialized)
        self._producer.flush(timeout=5)

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush(timeout=5)


def publish_telemetry(event: TelemetryEvent) -> None:
    producer = KafkaProducerClient()
    producer.produce(TOPIC_TELEMETRY, event.model_dump(mode="json"))
    producer.close()
