#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://127.0.0.1:8443"

echo "=== 1) Health check ==="
curl -k -s "${BASE_URL}/api/v1/health" | jq .

echo ""
echo "=== 2) Logowanie admina (bootstrap) ==="
ADMIN_RESP=$(curl -k -s -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation($u:String!,$p:String!){login(username:$u,password:$p){token username role}}","variables":{"u":"admin","p":"Admin123!"}}')
echo "$ADMIN_RESP" | jq .
ADMIN_TOKEN=$(echo "$ADMIN_RESP" | jq -r '.data.login.token')

echo ""
echo "=== 3) Utworzenie zadania ==="
curl -k -s -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: ${ADMIN_TOKEN}" \
  -d '{"query":"mutation($t:String!,$d:String!){createTask(title:$t,description:$d){id title description owner createdAt}}","variables":{"t":"Demo task","d":"Created during demo"}}' | jq .

echo ""
echo "=== 4) Zapytanie agregujace (me + tasks) ==="
curl -k -s -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: ${ADMIN_TOKEN}" \
  -d '{"query":"query { me { username role } tasks { id title owner } }"}' | jq .

echo ""
echo "=== 5) Audyt (admin only) ==="
curl -k -s -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: ${ADMIN_TOKEN}" \
  -d '{"query":"query { auditLogs(limit: 10) { id eventType actor result details createdAt } }"}' | jq .

echo ""
echo "=== 6) Rejestracja zwyklego uzytkownika ==="
USER_RESP=$(curl -k -s -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation($u:String!,$p:String!){register(username:$u,password:$p){token username role}}","variables":{"u":"bob","p":"User123!"}}')
echo "$USER_RESP" | jq .
USER_TOKEN=$(echo "$USER_RESP" | jq -r '.data.register.token')

echo ""
echo "=== 7) Proba audytu przez zwyklego uzytkownika (oczekiwany 403) ==="
curl -k -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST "${BASE_URL}/graphql" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: ${USER_TOKEN}" \
  -d '{"query":"query { auditLogs { id event_type } }"}' | jq .

echo ""
echo "=== 8) WebSocket ==="
echo "W osobnym terminalu uruchom:"
echo "  wscat -n -c \"wss://127.0.0.1:8443/ws/notifications?token=${ADMIN_TOKEN}\""
echo "Nastepnie utworz nowe zadanie przez panel lub curl, aby zobaczyc event task_created."

echo ""
echo "=== 9) TCP Chat ==="
echo "W osobnym terminalu uruchom serwer (jesli nie w kontenerze):"
echo "  python -m tcp.server"
echo "Nastepnie dwoch klientow:"
echo "  python -m tcp.client"
echo "Ustaw nicki (NICK:name) i wysylaj wiadomosci (MSG:text)."
