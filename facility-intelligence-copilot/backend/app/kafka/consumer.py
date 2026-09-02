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


import logging

logger = logging.getLogger(__name__)


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
            logger.error("Kafka consumer error: %s", message.error())
            raise RuntimeError(f"Kafka consumer error: {message.error()}")

        try:
            raw_value = message.value().decode("utf-8")
            payload = json.loads(raw_value)
            event = TelemetryEvent.model_validate(payload)
            self.service.process_event(event)
            return event
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode malformed JSON message from Kafka: %s", exc)
            return None
        except Exception as exc:
            logger.error("Failed to process telemetry message from Kafka: %s", exc)
            return None


    def close(self) -> None:
        if self._consumer is not None:
            self._consumer.close()
