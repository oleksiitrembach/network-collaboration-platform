# Projekt PAS - Network Collaboration Platform

Kompletny projekt akademicki spelniajacy wymagania kursu Programowanie Aplikacji Sieciowych:

1. Wlasna implementacja TCP client-server na socketach.
2. REST API po HTTP.
3. HTTPS (TLS, self-signed cert).
4. Architektura klient-serwer.
5. Nowoczesny mechanizm komunikacji: WebSocket (realtime).
6. GraphQL API do zapytan agregujacych.
7. Apache Kafka do zdarzen asynchronicznych.
8. Kontrola dostepu RBAC (role admin/user) i audit logging.
9. Konteneryzacja Docker i Docker Compose.
10. Dokumentacja architektury oraz analiza komunikacji.

## Funkcje bezpieczenstwa

1. RBAC: endpoint `GET /api/v1/admin/audit-logs` tylko dla roli admin.
2. Audit log: rejestracja zdarzen auth, RBAC, tworzenia zadan i WebSocket.
3. HTTPS/TLS: szyfrowanie komunikacji API i WebSocket.

## Struktura projektu

- `app/` - serwer aplikacyjny FastAPI (REST + WebSocket + auth + baza SQLite)
- `app/graphql_api.py` - warstwa GraphQL
- `app/events.py` - publikacja zdarzen do Kafka
- `tcp/` - niskopoziomowy serwer i klient TCP oparty na socketach
- `docs/` - dokumentacja architektury, analiza, scenariusz prezentacji
- `scripts/` - narzedzia pomocnicze (np. generowanie certyfikatow)
- `tests/` - testy automatyczne API
- `certs/` - certyfikat i klucz TLS (self-signed)
- `Dockerfile`, `docker-compose.yml` - konteneryzacja uslug

## Wymagania systemowe

1. Docker Desktop (Windows/macOS) lub Docker Engine + Docker Compose (Linux).

## Uruchomienie (Docker Compose - tryb domyslny)

1. Zbuduj i uruchom wszystkie uslugi:

```bash
docker compose up --build
```

2. Dzialanie w tle:

```bash
docker compose up -d --build
```

3. Zatrzymanie stosu:

```bash
docker compose down
```

4. Restart od czystego stanu (usuniecie wolumenow):

```bash
docker compose down -v
docker compose up --build
```

## Szybki dostep do backendu

0. UAT UI (panel testowy): `https://127.0.0.1:8443/`
1. Swagger UI: `https://127.0.0.1:8443/docs`
2. OpenAPI JSON: `https://127.0.0.1:8443/openapi.json`
3. Health: `https://127.0.0.1:8443/api/v1/health`

W trybie Docker domyslnie tworzony jest administrator bootstrapowy:
1. login: `admin`
2. haslo: `Admin123!`

## Testy

Testy aplikacyjne uruchamiane sa w kontenerze API:

```bash
docker compose run --rm -e PYTHONPATH=/app api pytest -q
```

Uruchamiane uslugi:
1. `api` - FastAPI HTTPS + REST + GraphQL + WebSocket
2. `tcp` - serwer TCP socket
3. `kafka` + `zookeeper` - warstwa asynchroniczna
4. `notification-service` - konsument eventow Kafki
5. `analytics-service` - konsument eventow Kafki (agregacja licznikow)

## Macierz zgodnosci z wymaganiami

1. TCP client/server socket: zaimplementowano (`tcp/client.py`, `tcp/server.py`).
2. REST API: zaimplementowano (`app/main.py`).
3. HTTPS/TLS: zaimplementowano (`app/run_https.py`, `scripts/generate_certs.py`).
4. WebSocket: zaimplementowano (`/ws/notifications`).
5. GraphQL: zaimplementowano (`/graphql`, `app/graphql_api.py`).
6. Message Queue (Kafka): zaimplementowano (`app/events.py`, `docker-compose.yml`).
7. Audit log + RBAC: zaimplementowano (`app/db.py`, `app/main.py`).

## Dokumentacja

1. Architektura i infogram: `docs/ARCHITECTURE.md`
2. Analiza komunikacji TCP/IP: `docs/ANALYSIS.md`
3. Przewodnik obrony: `docs/PRESENTATION_GUIDE.md`
4. Przyklady wywolan: `docs/API_EXAMPLES.md`
5. Instrukcja operacyjna krok po kroku: `docs/OPERATING_MANUAL_PL.md`
