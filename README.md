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
- `scripts/` - skrypty uruchamiania i generowania certyfikatow
- `tests/` - testy automatyczne API
- `certs/` - certyfikat i klucz TLS (self-signed)
- `Dockerfile`, `docker-compose.yml` - konteneryzacja uslug

## Wymagania systemowe

1. Python 3.11+

## Instrukcja uruchomienia (Windows)

1. Instalacja zaleznosci:

```powershell
C:/Users/alexp/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r requirements.txt
```

2. Generowanie certyfikatow:

```powershell
./scripts/generate_certs.ps1
```

3. Start API HTTPS:

```powershell
./scripts/run_api.ps1
```

4. Start TCP server (drugi terminal):

```powershell
./scripts/run_tcp_server.ps1
```

5. Start TCP client (trzeci terminal):

```powershell
./scripts/run_tcp_client.ps1
```

## Instrukcja uruchomienia (Linux)

1. Instalacja zaleznosci:

```bash
python -m pip install -r requirements.txt
```

2. Generowanie certyfikatow:

```bash
chmod +x scripts/*.sh
./scripts/generate_certs.sh
```

3. Start API HTTPS:

```bash
./scripts/run_api.sh
```

4. Start TCP server:

```bash
./scripts/run_tcp_server.sh
```

5. Start TCP client:

```bash
./scripts/run_tcp_client.sh
```

## Testy

```bash
pytest -q
```

## Uruchomienie kontenerowe (Docker Compose)

```bash
docker compose up --build
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
