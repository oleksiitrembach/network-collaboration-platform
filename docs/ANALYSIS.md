# Analiza komunikacji

## 1) Warstwy modelu TCP/IP

1. Warstwa aplikacji
   - GraphQL API (HTTP/1.1 over TLS)
   - WebSocket (upgrade HTTP -> stale polaczenie)
   - Protokol tekstowy TCP chat (`NICK`, `MSG`, `QUIT`)
   - Asynchroniczne zdarzenia Kafka (`tasks.events`, `security.audit`)

2. Warstwa transportowa
   - TCP dla HTTPS, WebSocket oraz serwera socketowego.

3. Warstwa internetowa
   - IP (IPv4, localhost 127.0.0.1 w scenariuszu lokalnym).

4. Warstwa dostepu do sieci
   - Ethernet/Wi-Fi (zalezne od hosta), w projekcie transparentna.

## 2) Komunikacja stanowa i bezstanowa

1. Bezstanowa
   - GraphQL API: kazde zadanie HTTP jest niezalezne; serwer nie trzyma kontekstu zapytania miedzy requestami.
   - Uwierzytelnienie realizowane przez token przesylany jawnie w kazdym wywolaniu (`X-Auth-Token`).

2. Stanowa
   - WebSocket: stale, dwukierunkowe polaczenie sesyjne klient-serwer.
   - TCP chat: stale polaczenie socketowe z utrzymywanym stanem klienta (nickname, aktywna sesja).

## 3) Porty i protokoly

1. `8443/tcp`
   - HTTPS GraphQL API (`/graphql`).
   - WebSocket endpoint (`wss://host:8443/ws/notifications`) po tym samym porcie.

2. `9000/tcp`
   - Wlasny serwer TCP chat oparty na socketach.

3. `9092/tcp`
   - Broker Apache Kafka (eventy asynchroniczne).

## 4) Bezpieczenstwo transmisji

- HTTPS/WSS realizowane przez certyfikat self-signed generowany skryptem `scripts/generate_certs.py`.
- Chroni poufnosc i integralnosc danych miedzy klientem i API.
- W srodowisku produkcyjnym self-signed nalezy zastapic certyfikatem zaufanego CA.

## 5) Kontrola dostepu i audyt

1. RBAC
   - Pierwszy zalozony uzytkownik otrzymuje role `admin`, kolejni `user`.
   - Zasob `auditLogs` w GraphQL jest dostepny tylko dla roli `admin`.

2. Audit logging
   - System zapisuje zdarzenia: rejestracja, logowanie, odmowy autoryzacji, utworzenie zadania, laczenie/rozlaczanie WebSocket.
   - Audyt wspiera analize incydentow i podnosi dojrzalosc projektu pod katem bezpieczenstwa.

## 6) Feature Checklist

1. Custom client-server implementation over raw TCP sockets
   - `tcp/server.py`, `tcp/client.py` (TCP sockets).

2. HTTP application server (GraphQL API)
   - `app/main.py` (FastAPI + Strawberry GraphQL).

3. HTTPS / TLS encryption
   - `app/run_https.py` + certificates in `certs/`.

4. Architecture diagram and protocol descriptions
   - `docs/ARCHITECTURE.md`.

5. Communication analysis (TCP/IP layers, ports, stateful vs stateless)
   - This document (`docs/ANALYSIS.md`).

6. Modern communication mechanisms
   - WebSocket (`/ws/notifications`), GraphQL (`/graphql`), Kafka (async events).
