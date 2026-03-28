from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("APP_DB_PATH", str(DATA_DIR / "app.db"))
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8443"))
TCP_HOST = os.getenv("TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.getenv("TCP_PORT", "9000"))

TLS_CERT_PATH = os.getenv("TLS_CERT_PATH", str(BASE_DIR / "certs" / "cert.pem"))
TLS_KEY_PATH = os.getenv("TLS_KEY_PATH", str(BASE_DIR / "certs" / "key.pem"))

KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_TOPIC_TASKS = os.getenv("KAFKA_TOPIC_TASKS", "tasks.events")
KAFKA_TOPIC_AUDIT = os.getenv("KAFKA_TOPIC_AUDIT", "security.audit")
