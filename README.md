# Network Collaboration Platform

A containerized network application demonstrating multiple communication protocols layered over TCP/IP:

- **GraphQL API** over HTTPS — unified application interface (queries & mutations)
- **WebSocket** (WSS) — real-time notifications
- **Raw TCP sockets** — custom low-level chat protocol
- **Apache Kafka** — asynchronous event streaming
- **RBAC + Audit logging** — role-based access control and security event tracking

## Security Features

1. **RBAC**: `auditLogs` GraphQL resource restricted to the `admin` role.
2. **Audit log**: persistent logging of authentication, authorization, task creation and WebSocket events.
3. **HTTPS/TLS**: encrypted API and WebSocket traffic using self-signed certificates (suitable for local/demo environments).

## Project Structure

- `app/` — FastAPI server (GraphQL + WebSocket + auth + SQLite)
- `app/graphql_api.py` — GraphQL schema (Strawberry): queries & mutations
- `app/events.py` — Kafka event publisher
- `tcp/` — low-level threaded TCP chat server & client
- `docs/` — architecture diagrams, protocol analysis, API examples
- `scripts/` — helper utilities (certificate generation, demo scenarios)
- `tests/` — automated API tests (pytest)
- `certs/` — self-signed TLS certificate and key
- `Dockerfile`, `docker-compose.yml` — full containerization

## Requirements

- Docker Desktop (Windows/macOS) or Docker Engine + Docker Compose (Linux)

## Quick Start (Docker Compose)

Build and run the entire stack:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up -d --build
```

Stop:

```bash
docker compose down
```

Clean restart (removes volumes):

```bash
docker compose down -v
docker compose up --build
```

## Access Points

- Web UI: `https://127.0.0.1:8443/`
- GraphQL endpoint: `https://127.0.0.1:8443/graphql`
- Health check: `https://127.0.0.1:8443/api/v1/health`

A bootstrap administrator is created automatically in Docker:
- login: `admin`
- password: `Admin123!`

## Running Tests

```bash
docker compose run --rm -e PYTHONPATH=/app api pytest -q
```

## Services Overview

1. `api` — FastAPI HTTPS + GraphQL + WebSocket
2. `tcp` — TCP socket chat server
3. `kafka` + `zookeeper` — asynchronous messaging layer
4. `notification-service` — Kafka consumer (event logging)
5. `analytics-service` — Kafka consumer (topic counters)

## Documentation

- Architecture & diagram: `docs/ARCHITECTURE.md`
- Protocol analysis (TCP/IP layers, ports, stateful vs stateless): `docs/ANALYSIS.md`
- API usage examples: `docs/API_EXAMPLES.md`
- Operational manual: `docs/OPERATING_MANUAL_PL.md`
- Showcase / demo guide: `docs/PRESENTATION_GUIDE.md`
