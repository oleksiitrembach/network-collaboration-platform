# Przyklady wywolan API

## 1) Rejestracja

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Secure123"}'
```

## 2) Logowanie

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Secure123"}'
```

## 3) Dodanie zadania

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <TOKEN>" \
  -d '{"title":"Przygotowac prezentacje projektu","description":"Implementacja i weryfikacja funkcjonalnosci"}'
```

## 4) Pobranie listy zadan

```bash
curl -k https://127.0.0.1:8443/api/v1/tasks \
  -H "X-Auth-Token: <TOKEN>"
```

## 5) WebSocket test (wscat)

```bash
wscat -n -c "wss://127.0.0.1:8443/ws/notifications?token=<TOKEN>"
```
