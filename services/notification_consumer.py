from __future__ import annotations

import json
import os
import time

from kafka import KafkaConsumer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPICS = [
    os.getenv("KAFKA_TOPIC_TASKS", "tasks.events"),
    os.getenv("KAFKA_TOPIC_AUDIT", "security.audit"),
]


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        *TOPICS,
        bootstrap_servers=[BOOTSTRAP],
        group_id="notification-service",
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def main() -> None:
    while True:
        try:
            consumer = create_consumer()
            print(f"[notification-service] Connected to Kafka at {BOOTSTRAP}")
            for message in consumer:
                payload = message.value
                print(f"[notification-service] topic={message.topic} payload={payload}")
            break
        except Exception as ex:
            print(f"[notification-service] Kafka unavailable: {ex}. Retrying in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    main()
