$BASE_URL = "https://127.0.0.1:8443"

Write-Host "=== 1) Health check ===" -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/health" -Method GET -SkipCertificateCheck
$response | ConvertTo-Json -Depth 3

Write-Host "`n=== 2) Logowanie admina (bootstrap) ===" -ForegroundColor Cyan
$adminBody = @{
    query = "mutation(`$u:String!,$p:String!){login(username:`$u,password:`$p){token username role}}"
    variables = @{ u = "admin"; p = "Admin123!" }
} | ConvertTo-Json -Depth 3 -Compress
$adminResp = Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Body $adminBody -SkipCertificateCheck
$adminResp | ConvertTo-Json -Depth 3
$adminToken = $adminResp.data.login.token

Write-Host "`n=== 3) Utworzenie zadania ===" -ForegroundColor Cyan
$taskBody = @{
    query = "mutation(`$t:String!,$d:String!){createTask(title:`$t,description:`$d){id title description owner createdAt}}"
    variables = @{ t = "Demo task"; d = "Created during demo" }
} | ConvertTo-Json -Depth 3 -Compress
$headers = @{ "X-Auth-Token" = $adminToken }
Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Headers $headers -Body $taskBody -SkipCertificateCheck | ConvertTo-Json -Depth 3

Write-Host "`n=== 4) Zapytanie agregujace (me + tasks) ===" -ForegroundColor Cyan
$qBody = @{
    query = "query { me { username role } tasks { id title owner } }"
} | ConvertTo-Json -Depth 3 -Compress
Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Headers $headers -Body $qBody -SkipCertificateCheck | ConvertTo-Json -Depth 3

Write-Host "`n=== 5) Audyt (admin only) ===" -ForegroundColor Cyan
$auditBody = @{
    query = "query { auditLogs(limit: 10) { id event_type actor result details createdAt } }"
} | ConvertTo-Json -Depth 3 -Compress
Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Headers $headers -Body $auditBody -SkipCertificateCheck | ConvertTo-Json -Depth 3

Write-Host "`n=== 6) Rejestracja zwyklego uzytkownika ===" -ForegroundColor Cyan
$userBody = @{
    query = "mutation(`$u:String!,$p:String!){register(username:`$u,password:`$p){token username role}}"
    variables = @{ u = "bob"; p = "User123!" }
} | ConvertTo-Json -Depth 3 -Compress
$userResp = Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Body $userBody -SkipCertificateCheck
$userResp | ConvertTo-Json -Depth 3
$userToken = $userResp.data.register.token

Write-Host "`n=== 7) Proba audytu przez zwyklego uzytkownika (oczekiwany 403) ===" -ForegroundColor Cyan
$forbiddenHeaders = @{ "X-Auth-Token" = $userToken }
try {
    Invoke-RestMethod -Uri "$BASE_URL/graphql" -Method POST -ContentType "application/json" -Headers $forbiddenHeaders -Body $auditBody -SkipCertificateCheck | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Blad (oczekiwany): $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
}

Write-Host "`n=== 8) WebSocket ===" -ForegroundColor Cyan
Write-Host "W osobnym terminalu uruchom:"
Write-Host "  wscat -n -c \"wss://127.0.0.1:8443/ws/notifications?token=$adminToken\""
Write-Host "Nastepnie utworz nowe zadanie przez panel lub curl, aby zobaczyc event task_created."

Write-Host "`n=== 9) TCP Chat ===" -ForegroundColor Cyan
Write-Host "W osobnym terminalu uruchom serwer (jesli nie w kontenerze):"
Write-Host "  python -m tcp.server"
Write-Host "Nastepnie dwoch klientow:"
Write-Host "  python -m tcp.client"
Write-Host "Ustaw nicki (NICK:name) i wysylaj wiadomosci (MSG:text)."
