from __future__ import annotations

import json
import os
import time
from collections import Counter

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
        group_id="analytics-service",
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def main() -> None:
    counters = Counter()
    while True:
        try:
            consumer = create_consumer()
            print(f"[analytics-service] Connected to Kafka at {BOOTSTRAP}")
            for message in consumer:
                counters[message.topic] += 1
                print(f"[analytics-service] topic={message.topic} count={counters[message.topic]}")
            break
        except Exception as ex:
            print(f"[analytics-service] Kafka unavailable: {ex}. Retrying in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    main()
