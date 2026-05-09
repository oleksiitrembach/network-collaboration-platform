# Showcase & Demo Guide

## Project Goal

This application demonstrates three network communication styles in a single architecture:
1. **GraphQL over HTTPS** — stateless application interface (queries & mutations).
2. **WebSocket** — stateful real-time communication.
3. **Raw TCP socket** — low-level client-server communication.

Additionally, the system uses **Apache Kafka** for asynchronous event processing.

## Suggested Demo Flow (8–12 minutes)

1. **Start the stack**
   - `docker compose up --build`
   - Highlight all running containers: API, TCP, Kafka, Zookeeper, consumers.

2. **Authentication via GraphQL**
   - Demonstrate `mutation { register(...) }` and `mutation { login(...) }` to obtain a token.

3. **GraphQL Operations**
   - Show `mutation { createTask(...) }` and `query { tasks { ... } }` using the `X-Auth-Token` header.
   - Run an aggregated query: `query { me { ... } tasks { ... } auditLogs { ... } }`.

4. **Real-time Notifications**
   - Open a WebSocket client and trigger a `task_created` event by adding a task through GraphQL.

5. **Low-level TCP Chat**
   - Launch two TCP clients and exchange messages through the custom `NICK`/`MSG`/`QUIT` protocol.

6. **Asynchronous Events (optional)**
   - Show consumer logs (`notification-service`, `analytics-service`) processing Kafka streams.

## Typical Q&A

1. **Why GraphQL instead of REST?**
   - GraphQL lets the client specify exactly which fields it needs, eliminating over-fetching and under-fetching, and provides a single unified interface for all operations.

2. **Why is WebSocket stateful?**
   - It maintains an active session and persistent connection between parties, enabling server-pushed events.

3. **What does TLS provide?**
   - Encryption, integrity, and server authentication; it reduces the risk of eavesdropping and data tampering.

4. **Why a separate TCP server when there is an API?**
   - It demonstrates the ability to work at the socket level, outside the abstractions of an HTTP framework.

5. **What trade-offs were made?**
   - SQLite and a simple session model were chosen to keep the project deterministic and easy to run in isolated environments.
   - Kafka runs without replication (single broker), which is sufficient for demonstration purposes.

## Quality Checklist

1. HTTPS and WebSocket run on the same server.
2. Independent TCP client/server works on raw sockets.
3. GraphQL is the sole application interface (mutations + queries).
4. Automated tests cover the API.
5. Documentation explains protocols, ports, and TCP/IP layers.
6. The demo shows a real end-to-end data flow.
