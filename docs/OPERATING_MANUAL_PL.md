# Instrukcja operacyjna projektu (PL)

## 1. Zakres systemu i komponenty

Projekt to aplikacja klient-serwer uruchamiana domyslnie przez Docker Compose.

1. REST API po HTTPS (port 8443)
- Rejestracja, logowanie, zadania, endpoint administracyjny audytu.

2. WebSocket po WSS (port 8443, sciezka `/ws/notifications`)
- Powiadomienia czasu rzeczywistego po utworzeniu zadania.

3. TCP socket server (port 9000)
- Niskopoziomowy kanal czatu (`NICK`, `MSG`, `QUIT`).

4. GraphQL (`/graphql`)
- Zapytania agregujace (`me`, `tasks`, `audit_logs`).

5. Kafka + konsumenci
- Eventy `tasks.events` i `security.audit`.
- Serwisy `notification-service` i `analytics-service` przetwarzaja strumienie zdarzen.

6. RBAC + audit log
- Role `admin` i `user`.
- Rejestrowanie zdarzen bezpieczenstwa i operacji biznesowych.

## 2. Wymagania

1. Docker Desktop (Windows/macOS) lub Docker Engine + Docker Compose (Linux).
2. Terminal (PowerShell lub bash).

## 3. Uruchomienie systemu (Docker-first)

### Krok 1: start calego stosu

```bash
docker compose up --build
```

Oczekiwany efekt:
- Wszystkie kontenery startuja bez bledu.
- Dostepne uslugi: `api`, `tcp`, `kafka`, `zookeeper`, `notification-service`, `analytics-service`.

### Krok 2: sprawdzenie statusu kontenerow

```bash
docker compose ps
```

Oczekiwany efekt:
- Kazda usluga ma status `Up`.

### Krok 3: opcjonalny restart od czystego stanu

```bash
docker compose down -v
docker compose up --build
```

Stosowac przed pokazem, jezeli chcesz deterministycznie uzyskac pierwszego uzytkownika z rola `admin`.

## 4. Manualny scenariusz UAT (uzytkownik koncowy)

### 4.1 Health check

```bash
curl -k https://127.0.0.1:8443/api/v1/health
```

Oczekiwany efekt:
- Kod `200` i odpowiedz ze statusem `ok`.

### 4.2 Logowanie kontem administracyjnym (bootstrap)

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"Admin123!\"}"
```

Oczekiwany efekt:
- Kod `200`.
- Odpowiedz zawiera `token` i role `admin`.

### 4.3 Utworzenie zadania (REST)

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/tasks -H "Content-Type: application/json" -H "X-Auth-Token: <TOKEN_ADMIN>" -d "{\"title\":\"Walidacja projektu\",\"description\":\"Scenariusz obrony\"}"
```

Oczekiwany efekt:
- Kod `201` i obiekt zadania.

### 4.4 Zapytanie GraphQL

```bash
curl -k -X POST https://127.0.0.1:8443/graphql -H "Content-Type: application/json" -H "X-Auth-Token: <TOKEN_ADMIN>" -d "{\"query\":\"query { me { username role } tasks { id title owner } }\"}"
```

Oczekiwany efekt:
- Kod `200` i dane `me` oraz `tasks`.

### 4.5 Test RBAC

1. Zarejestruj drugiego uzytkownika.
2. Uzyj jego tokenu do `GET /api/v1/admin/audit-logs`.

Oczekiwany efekt:
- Kod `403 Forbidden`.

### 4.6 Dostep do audytu jako admin

```bash
curl -k https://127.0.0.1:8443/api/v1/admin/audit-logs -H "X-Auth-Token: <TOKEN_ADMIN>"
```

Oczekiwany efekt:
- Kod `200` i lista zdarzen.

### 4.7 Test WebSocket

1. Otworz klienta WebSocket pod adresem `wss://127.0.0.1:8443/ws/notifications?token=<TOKEN_ADMIN>`.
2. Utworz nowe zadanie przez REST.

Oczekiwany efekt:
- Na kanale WebSocket pojawia sie event `task_created`.

### 4.8 Test TCP

1. Otworz dwa klienty TCP i ustaw nicki.
2. Wyslij wiadomosc z pierwszego klienta.

Oczekiwany efekt:
- Drugi klient odbiera broadcast.

## 5. Walidacja automatyczna

```bash
docker compose run --rm -e PYTHONPATH=/app api pytest -q
```

Oczekiwany efekt:
- Wszystkie testy przechodza.

## 6. Najczestsze problemy

1. Port 8443 lub 9000 zajety
- Zwolnij porty albo zatrzymaj kolidujace procesy.

2. Docker daemon nie jest uruchomiony
- Uruchom Docker Desktop i ponow polecenie `docker compose up --build`.

3. Brak roli `admin` dla nowego konta
- Wykonaj login kontem bootstrapowym `admin` / `Admin123!`.

## 7. Checklist przed testami/obrona

1. Czy wszystkie uslugi sa `Up` po `docker compose ps`? TAK/NIE.
2. Czy health check zwraca `200`? TAK/NIE.
3. Czy REST, GraphQL i WebSocket dzialaja? TAK/NIE.
4. Czy RBAC blokuje uzytkownika `user` na endpointach admin? TAK/NIE.
5. Czy TCP chat dziala miedzy dwoma klientami? TAK/NIE.
6. Czy testy automatyczne przechodza? TAK/NIE.
