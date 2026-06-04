# PostgreSQL Backup and Restore Runbook

This runbook protects Repo B application data stored in PostgreSQL: users, roles, refresh tokens, audit logs, saved searches, alert workflow, notifications, and cases. Repo A remains the source for raw Wazuh alerts and agent data.

## Scope

Back up:

- `soc-postgres` PostgreSQL database
- all application tables managed by Alembic
- data needed to preserve analyst workflow and audit history

Do not store database dumps in git. Local dump files are written under `backups/postgres/`, which is ignored by `.gitignore`.

## Backup

Run from `soc-dashboard` while Docker Compose is up:

```powershell
.\scripts\backup_postgres.ps1
```

Optional output directory:

```powershell
.\scripts\backup_postgres.ps1 -OutputDir "D:\soc-dashboard-backups"
```

The script:

1. Reads `POSTGRES_DB` and `POSTGRES_USER` from `soc-postgres`.
2. Runs `pg_dump` in custom format with `-Fc`.
3. Copies the dump to the host.
4. Removes the temporary dump from the container.

Expected output:

```text
Backup created: <path>\soc-dashboard-<database>-<timestamp>.dump
Database: <database>
Size bytes: <number>
```

## Backup Cadence

For internal pilot:

- before every schema migration
- before importing or editing pilot users in bulk
- before a demo or user acceptance session
- daily during active pilot usage

Recommended retention:

- keep daily backups for 7 days
- keep weekly backups for 4 weeks
- move long-lived backups off the application host

## Restore

Restore overwrites data in the target database. Do this only after confirming the current database can be replaced.

Run from `soc-dashboard`:

```powershell
.\scripts\restore_postgres.ps1 -BackupFile "backups\postgres\soc-dashboard-soc_dashboard-YYYYMMDD-HHMMSS.dump" -ConfirmRestore
```

The script:

1. Copies the dump into `soc-postgres`.
2. Runs `pg_restore --clean --if-exists --no-owner`.
3. Removes the temporary restore file from the container.
4. Runs `alembic upgrade head` from `soc-backend`.

## Restore Verification

After restore:

```powershell
docker compose ps
curl http://localhost:8000/health
```

Then run:

```powershell
$env:PILOT_TEST_USERNAME = "<superadmin-username>"
$env:PILOT_TEST_PASSWORD = "<superadmin-password>"
python -m unittest discover -s tests -v
```

Also run the smoke test:

```powershell
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
```

## Disposable Restore Drill

Use this command to verify that a dump can restore into a temporary PostgreSQL container without touching the main `soc-postgres` database:

```powershell
.\scripts\restore_drill_postgres.ps1
```

Optional explicit dump:

```powershell
.\scripts\restore_drill_postgres.ps1 -BackupFile "backups\postgres\soc-dashboard-soc_dashboard-YYYYMMDD-HHMMSS.dump"
```

The drill:

1. Starts a disposable `postgres:16-alpine` container.
2. Restores the backup dump into a temporary database.
3. Verifies public table count, Alembic version rows, user count, and case count.
4. Stops and removes the disposable container.

## Operational Notes

- A backup verifies that a dump can be created. A restore drill verifies that the dump is actually usable.
- For pilot, run the disposable restore drill after backup creation and before handoff.
- Keep `.env` and database dumps out of git.
- Treat dumps as sensitive because they contain users, audit history, saved workflow, and cases.
- If restore fails midway, recreate the target database/volume from a known backup and re-run restore.
