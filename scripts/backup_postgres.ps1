param(
    [string]$OutputDir = "backups/postgres"
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$database = (docker compose exec -T soc-postgres printenv POSTGRES_DB).Trim()
$username = (docker compose exec -T soc-postgres printenv POSTGRES_USER).Trim()

if (-not $database -or -not $username) {
    throw "Unable to read POSTGRES_DB or POSTGRES_USER from soc-postgres."
}

$containerDumpPath = "/tmp/soc-dashboard-$timestamp.dump"
$localDumpPath = Join-Path $OutputDir "soc-dashboard-$database-$timestamp.dump"

docker compose exec -T soc-postgres pg_dump -U $username -d $database -Fc -f $containerDumpPath
docker compose cp "soc-postgres:$containerDumpPath" $localDumpPath
docker compose exec -T soc-postgres rm -f $containerDumpPath

$resolvedDump = Resolve-Path $localDumpPath
$sizeBytes = (Get-Item $resolvedDump).Length

Write-Output "Backup created: $resolvedDump"
Write-Output "Database: $database"
Write-Output "Size bytes: $sizeBytes"
