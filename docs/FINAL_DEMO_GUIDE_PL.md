# Ostateczna instrukcja pokazu aplikacji

## 1. Cel pokazu

Pokaz ma potwierdzic:

1. dzialanie aplikacji webowej,
2. bezpieczenstwo (TLS + RBAC + audit),
3. realtime (WebSocket),
4. asynchronicznosc (Kafka),
5. niezalezny modul socketowy TCP.

## 2. Przygotowanie (1 minuta)

1. Uruchom srodowisko:

```bash
docker compose up -d --build
```

2. Sprawdz status:

```bash
docker compose ps
```

3. Otworz panel aplikacji:

- `https://127.0.0.1:8443/`

## 3. Scenariusz demo krok po kroku

### Krok 1: logowanie admin

1. W panelu kliknij logowanie (`admin` / `Admin123!`).
2. Pokaz komunikat o ustawionym tokenie.

Co to znaczy:
- user ma aktywna sesje i moze wykonywac endpointy chronione.

### Krok 2: status systemu

1. Kliknij sprawdzenie statusu.

Co to znaczy:
- API dziala i odpowiada poprawnie.

### Krok 3: tworzenie zadania (REST)

1. Dodaj nowe zadanie.
2. Odswiez liste zadan.

Co to znaczy:
- operacje biznesowe zapis/odczyt dzialaja.

### Krok 4: zapytanie GraphQL

1. Uruchom zapytanie `me + tasks`.

Co to znaczy:
- GraphQL agreguje dane jednym requestem.

### Krok 5: audit log (admin)

1. Pobierz dziennik zdarzen.

Co to znaczy:
- system rejestruje kluczowe operacje.

### Krok 6: WebSocket realtime

1. Polacz WebSocket w panelu.
2. Utworz kolejne zadanie.
3. Pokaz event `task_created`.

Co to znaczy:
- dziala komunikacja push w czasie rzeczywistym.

### Krok 7: RBAC

1. Zarejestruj zwyklego usera.
2. Zaloguj go i pobierz token usera.
3. Sprobuj wejsc userem na endpoint admin audit.

Oczekiwany wynik:
- `403 Forbidden`.

Co to znaczy:
- kontrola dostepu po roli dziala poprawnie.

### Krok 8: TCP socket demo

1. Otworz dwa terminale i uruchom klienta TCP:

```bash
docker compose exec tcp python -m tcp.client
```

2. Ustaw nicki i wyslij wiadomosc.
3. Pokaz, ze drugi klient odbiera broadcast.

Co to znaczy:
- niezalezny modul socketowy client-server dziala.

### Krok 9: Kafka (dowod asynchronicznosci)

1. Pokaz logi konsumentow:

```bash
docker compose logs notification-service --tail 30
docker compose logs analytics-service --tail 30
```

Co to znaczy:
- eventy publikowane przez API sa konsumowane asynchronicznie.

## 4. Co powiedziec przy podsumowaniu

1. Aplikacja laczy REST/GraphQL/WebSocket/TCP/Kafka w jednej architekturze.
2. TLS zabezpiecza transport, RBAC i audit zabezpieczaja warstwe aplikacyjna.
3. Wymagania formalne socket + HTTP + HTTPS + analiza + diagram sa spelnione.

## 5. Plan awaryjny (gdy cos nie zaskoczy)

1. Brak odpowiedzi UI po starcie:
- odczekaj 10-20 sekund i odswiez strone.

2. Problem z rola admin po wielu restartach:

```bash
docker compose down -v
docker compose up -d --build
```

3. Test automatyczny przed pokazem:

```bash
docker compose run --rm -e PYTHONPATH=/app api pytest -q
```
