param(
    [string]$BackupFile = "",
    [string]$PostgresImage = "postgres:16-alpine",
    [switch]$KeepContainer
)

$ErrorActionPreference = "Stop"

if (-not $BackupFile) {
    $latestBackup = Get-ChildItem -LiteralPath "backups/postgres" -Filter "*.dump" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $latestBackup) {
        throw "No backup dump found under backups/postgres. Run .\scripts\backup_postgres.ps1 first."
    }
    $BackupFile = $latestBackup.FullName
}

if (-not (Test-Path -LiteralPath $BackupFile)) {
    throw "Backup file does not exist: $BackupFile"
}

$resolvedBackup = Resolve-Path -LiteralPath $BackupFile
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$containerName = "soc-postgres-restore-drill-$timestamp"
$database = "soc_restore_drill"
$username = "soc_restore_drill"
$password = "soc_restore_drill_password"
$containerRestorePath = "/tmp/soc-dashboard-restore-drill.dump"

Write-Output "Starting disposable restore drill container: $containerName"
docker run --rm `
    --name $containerName `
    -e POSTGRES_DB=$database `
    -e POSTGRES_USER=$username `
    -e POSTGRES_PASSWORD=$password `
    -d $PostgresImage | Out-Null

try {
    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker exec $containerName pg_isready -U $username -d $database *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "Restore drill PostgreSQL container did not become ready."
    }

    docker cp $resolvedBackup "${containerName}:$containerRestorePath"
    docker exec $containerName pg_restore -U $username -d $database --clean --if-exists --no-owner $containerRestorePath

    $tableCount = (docker exec $containerName psql -U $username -d $database -tAc "select count(*) from information_schema.tables where table_schema = 'public';").Trim()
    $migrationCount = (docker exec $containerName psql -U $username -d $database -tAc "select count(*) from alembic_version;").Trim()
    $userCount = (docker exec $containerName psql -U $username -d $database -tAc "select count(*) from users;").Trim()
    $caseCount = (docker exec $containerName psql -U $username -d $database -tAc "select count(*) from cases;").Trim()

    if ([int]$tableCount -lt 1) {
        throw "Restore completed but no public tables were found."
    }
    if ([int]$migrationCount -lt 1) {
        throw "Restore completed but alembic_version is empty."
    }
    if ([int]$userCount -lt 1) {
        throw "Restore completed but users table is empty."
    }

    Write-Output "Restore drill OK"
    Write-Output "Backup file: $resolvedBackup"
    Write-Output "Database: $database"
    Write-Output "Public tables: $tableCount"
    Write-Output "Alembic rows: $migrationCount"
    Write-Output "Users: $userCount"
    Write-Output "Cases: $caseCount"
}
finally {
    if ($KeepContainer) {
        Write-Output "Keeping disposable container for inspection: $containerName"
    } else {
        docker stop $containerName *> $null
        Write-Output "Disposable restore drill container removed: $containerName"
    }
}
