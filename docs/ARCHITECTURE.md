# Diagram architektury systemu

## Infogram (Mermaid)

```mermaid
flowchart TB
    subgraph Clients[Klienci]
        U1[Przegladarka / Postman]
        U2[Klient TCP CLI]
    end

    subgraph Platform[Network Collaboration Platform]
        API[FastAPI REST API\nHTTPS :8443]
        GQL[GraphQL API\n/graphql]
        WS[WebSocket Gateway\nWSS :8443/ws/notifications]
        APP[(Logika aplikacji)]
        DB[(SQLite)]
        KAFKA[(Apache Kafka)]
        NS[Notification Service\nKafka Consumer]
        AS[Analytics Service\nKafka Consumer]
        SEC[(RBAC + Audit Log)]
        TCP[TCP Socket Server\n:9000]
    end

    U1 -->|HTTPS REST| API
    U1 -->|HTTPS GraphQL| GQL
    U1 -->|WSS realtime| WS
    U2 -->|TCP socket| TCP

    API --> APP
    GQL --> APP
    WS --> APP
    APP --> SEC
    APP --> DB
    APP -->|tasks.events + security.audit| KAFKA
    KAFKA --> NS
    KAFKA --> AS
    APP -->|zdarzenia task_created| WS
```

## Komponenty i role

1. FastAPI REST API (HTTPS)
- Endpointy rejestracji, logowania i zarzadzania zadaniami.
- Interfejs bezstanowy: kazde zadanie REST niesie token sesji w naglowku.

2. WebSocket Gateway
- Utrzymuje stale polaczenie z klientem.
- Dostarcza powiadomienia w czasie rzeczywistym po utworzeniu zadania.

3. GraphQL API
- Zapytania agregujace dane aplikacyjne (`me`, `tasks`, `audit_logs`).
- Dostep oparty o ten sam token uwierzytelniajacy co REST.

4. TCP Socket Server
- Niskopoziomowy serwer czatu oparty bezposrednio na interfejsie socket.
- Wlasny protokol tekstowy: `NICK:<name>`, `MSG:<text>`, `QUIT`.

5. SQLite
- Trwala baza danych dla uzytkownikow, sesji i zadan.

6. Apache Kafka
- Publikacja zdarzen asynchronicznych (`tasks.events`, `security.audit`).
- Integracja z API w trybie opcjonalnym (dzialanie bez brokera nie powoduje awarii aplikacji).

7. Notification Service
- Konsument zdarzen Kafki uruchamiany jako osobny serwis kontenerowy.
- Odpowiada za przetwarzanie strumienia zdarzen powiadomien.

8. Analytics Service
- Konsument zdarzen Kafki odpowiedzialny za agregacje licznikow i obserwowalnosc przeplywu.

9. Warstwa bezpieczenstwa (RBAC + Audit)
- RBAC: role `admin` i `user` do kontroli dostepu do endpointow administracyjnych.
- Audit log: trwałe logowanie operacji uwierzytelniania, autoryzacji i zdarzen WebSocket.