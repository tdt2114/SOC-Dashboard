param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [int]$LogTail = 20
)

$ErrorActionPreference = "Stop"

Write-Output "Runtime health report"
Write-Output "Backend URL: $BackendUrl"
Write-Output "Frontend URL: $FrontendUrl"
Write-Output ""

Write-Output "Docker Compose services:"
docker compose ps

Write-Output ""
Write-Output "Backend /health:"
try {
    $backendHealth = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get -TimeoutSec 10
    $backendHealth | ConvertTo-Json -Compress
}
catch {
    Write-Output "Backend health check failed: $($_.Exception.Message)"
    Write-Output ""
    Write-Output "Recent soc-backend logs:"
    docker compose logs --tail $LogTail soc-backend
    throw
}

Write-Output ""
Write-Output "Frontend /login:"
try {
    $frontendResponse = Invoke-WebRequest -Uri "$FrontendUrl/login" -Method Head -UseBasicParsing -TimeoutSec 10
    Write-Output "StatusCode: $($frontendResponse.StatusCode)"
}
catch {
    Write-Output "Frontend health check failed: $($_.Exception.Message)"
    Write-Output ""
    Write-Output "Recent soc-frontend logs:"
    docker compose logs --tail $LogTail soc-frontend
    throw
}

Write-Output ""
Write-Output "Recent container logs:"
docker compose logs --tail $LogTail soc-backend soc-frontend soc-postgres

Write-Output ""
Write-Output "Runtime health report completed."
