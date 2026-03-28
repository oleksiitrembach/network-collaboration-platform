from __future__ import annotations

import json
import logging
from typing import Any

from kafka import KafkaProducer

from app.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_ENABLED

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self, enabled: bool = KAFKA_ENABLED, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS) -> None:
        self.enabled = enabled
        self.bootstrap_servers = bootstrap_servers
        self._producer: KafkaProducer | None = None

        if self.enabled:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=[self.bootstrap_servers],
                    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                    key_serializer=lambda key: key.encode("utf-8") if key else None,
                    acks="all",
                    retries=3,
                )
            except Exception as ex:
                logger.warning("Kafka producer initialization failed: %s", ex)
                self._producer = None

    def publish(self, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
        if not self.enabled or self._producer is None:
            return

        try:
            self._producer.send(topic, key=key, value=payload)
            self._producer.flush(timeout=1.0)
        except Exception as ex:
            logger.warning("Kafka publish failed for topic '%s': %s", topic, ex)

    def close(self) -> None:
        if self._producer is None:
            return

        try:
            self._producer.flush(timeout=1.0)
            self._producer.close(timeout=1.0)
        except Exception:
            pass
