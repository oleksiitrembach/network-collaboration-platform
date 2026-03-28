# Przewodnik do prezentacji i obrony

## Cel projektu

Aplikacja prezentuje trzy style komunikacji sieciowej w jednej architekturze:
1. REST po HTTPS (komunikacja aplikacyjna, bezstanowa).
2. WebSocket (komunikacja realtime, stanowa).
3. Czysty TCP socket (niskopoziomowa komunikacja klient-serwer).

## Scenariusz prezentacji (8-12 minut)

1. Start serwerow
- Nalezy uruchomic TCP server na porcie 9000.
- Nalezy uruchomic API po HTTPS na porcie 8443.

2. Rejestracja i logowanie
- Nalezy przedstawic `POST /api/v1/auth/register` oraz otrzymanie tokenu.

3. Operacje REST
- Nalezy przedstawic `POST /api/v1/tasks` i `GET /api/v1/tasks` z naglowkiem `X-Auth-Token`.

4. Realtime
- Nalezy otworzyc klienta WebSocket i przedstawic zdarzenie `task_created` po dodaniu zadania.

5. Socket low-level
- Nalezy uruchomic dwoch klientow TCP i przedstawic wymiane wiadomosci przez serwer.

## Typowe pytania od prowadzacego i odpowiedzi

1. Dlaczego REST jest bezstanowy?
- Bo kazdy request zawiera komplet informacji potrzebnych do obslugi (token, payload), a serwer nie wymaga kontekstu poprzednich requestow.

2. Dlaczego WebSocket jest stanowy?
- Bo utrzymuje aktywna sesje i stale polaczenie miedzy stronami do pushowania zdarzen.

3. Co daje TLS?
- Szyfrowanie, integralnosc i uwierzytelnienie serwera; ogranicza ryzyko podslychu i modyfikacji danych.

4. Po co osobny TCP server skoro jest API?
- To wymaganie kursu pokazujace umiejetnosc pracy na poziomie socket, poza abstrakcja HTTP frameworka.

5. Jakie kompromisy projektowe zostaly podjete?
- Wybrano SQLite i prosty model sesji, aby projekt byl deterministyczny i latwy do uruchomienia na laboratorium.

## Kryteria na wysoka ocene (checklista)

1. Dziala HTTPS i WebSocket w jednym serwerze.
2. Dziala niezalezny TCP client/server na socketach.
3. Kod ma testy automatyczne dla API.
4. Dokumentacja wyjasnia protokoly, porty i warstwy TCP/IP.
5. Prezentacja pokazuje realny przeplyw danych end-to-end.
