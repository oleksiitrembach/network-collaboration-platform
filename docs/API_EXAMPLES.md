# Przyklady wywolan API (GraphQL)

Wszystkie operacje aplikacyjne odbywaja sie przez endpoint GraphQL `POST /graphql`.
Token uwierzytelniajacy przekazywany jest w naglowku `X-Auth-Token`.

## 1) Rejestracja

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation($u:String!,$p:String!){register(username:$u,password:$p){token username role}}","variables":{"u":"alice","p":"Secure123"}}'
```

## 2) Logowanie

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation($u:String!,$p:String!){login(username:$u,password:$p){token username role}}","variables":{"u":"alice","p":"Secure123"}}'
```

## 3) Utworzenie zadania

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <TOKEN>" \
  -d '{"query":"mutation($t:String!,$d:String!){createTask(title:$t,description:$d){id title description owner createdAt}}","variables":{"t":"Przygotowac prezentacje","d":"Implementacja i weryfikacja funkcjonalnosci"}}'
```

## 4) Pobranie listy zadan

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <TOKEN>" \
  -d '{"query":"query { tasks { id title description owner createdAt } }"}'
```

## 5) Pobranie dziennika audytu (tylko admin)

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <TOKEN_ADMIN>" \
  -d '{"query":"query { auditLogs(limit: 100) { id eventType actor result details createdAt } }"}'
```

## 6) GraphQL — zapytanie agregujace (me + tasks)

```bash
curl -k -X POST https://127.0.0.1:8443/graphql \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <TOKEN>" \
  -d '{"query":"query { me { username role } tasks { id title owner } }"}'
```

## 7) WebSocket test (wscat)

```bash
wscat -n -c "wss://127.0.0.1:8443/ws/notifications?token=<TOKEN>"
```
