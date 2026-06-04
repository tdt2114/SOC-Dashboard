param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,

    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"

if (-not $ConfirmRestore) {
    throw "Restore is destructive. Re-run with -ConfirmRestore after confirming the target database can be overwritten."
}

if (-not (Test-Path -LiteralPath $BackupFile)) {
    throw "Backup file does not exist: $BackupFile"
}

$resolvedBackup = Resolve-Path -LiteralPath $BackupFile
$database = (docker compose exec -T soc-postgres printenv POSTGRES_DB).Trim()
$username = (docker compose exec -T soc-postgres printenv POSTGRES_USER).Trim()
$containerRestorePath = "/tmp/soc-dashboard-restore.dump"

if (-not $database -or -not $username) {
    throw "Unable to read POSTGRES_DB or POSTGRES_USER from soc-postgres."
}

Write-Output "Restoring $resolvedBackup into database $database."
docker compose cp $resolvedBackup "soc-postgres:$containerRestorePath"
docker compose exec -T soc-postgres pg_restore -U $username -d $database --clean --if-exists --no-owner $containerRestorePath
docker compose exec -T soc-postgres rm -f $containerRestorePath
docker compose exec -T soc-backend alembic upgrade head

Write-Output "Restore completed and migrations are at head."
