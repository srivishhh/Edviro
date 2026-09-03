from __future__ import annotations

import json

from app.kafka.config import get_kafka_config
from app.kafka.topics import TOPIC_TELEMETRY
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import TelemetryService

try:
    from confluent_kafka import Consumer
except ImportError:  # pragma: no cover
    Consumer = None


class KafkaConsumerClient:
    def __init__(self, bootstrap_servers: str | None = None, service: TelemetryService | None = None):
        self.config = get_kafka_config()
        self.bootstrap_servers = bootstrap_servers or self.config.bootstrap_servers
        self.service = service or TelemetryService()
        self._consumer = None

        if Consumer is not None:
            self._consumer = Consumer({
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": "facility-telemetry-group",
                "auto.offset.reset": "earliest",
                "security.protocol": self.config.security_protocol,
            })
            self._consumer.subscribe([TOPIC_TELEMETRY])

    def poll_one(self) -> TelemetryEvent | None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is unavailable because confluent-kafka is not installed.")

        message = self._consumer.poll(timeout=1.0)
        if message is None:
            return None
        if message.error():
            raise RuntimeError(f"Kafka consumer error: {message.error()}")

        payload = json.loads(message.value().decode("utf-8"))
        event = TelemetryEvent.model_validate(payload)
        self.service.process_event(event)
        return event

    def close(self) -> None:
        if self._consumer is not None:
            self._consumer.close()
