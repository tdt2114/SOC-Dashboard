# Production Restore Approval Procedure

This procedure controls destructive PostgreSQL restores for Repo B. It applies to production and production-like pilot environments where user, audit, workflow, and case data matter.

Use this procedure with [POSTGRES_BACKUP_RESTORE.md](POSTGRES_BACKUP_RESTORE.md). The restore script already requires `-ConfirmRestore`; this document defines the approval and evidence required before that flag is used.

## Restore Is Allowed Only When

At least one condition is true:

- the active database is corrupted or unavailable
- a migration or deployment damaged Repo B application data
- an approved rollback requires returning to a known backup
- a pilot handoff rehearsal explicitly needs a production-like restore test

Do not restore production to clean up old test cases. Use the case retention workflow first.

## Required Roles

| Role | Responsibility |
| --- | --- |
| Requester | Explains why restore is needed and what data may be lost |
| Approver | Confirms restore is justified and accepts data-loss risk |
| Operator | Runs backup, restore drill, restore, and verification commands |
| Verifier | Confirms app health, login, role access, cases, audit logs, and exports after restore |

For a small team, one person can be operator and verifier, but the approver should be separate from the operator.

## Pre-Restore Approval Checklist

Record these items in the issue, handoff note, or incident log before running restore:

- target environment
- restore reason
- selected backup file path and timestamp
- expected data-loss window
- current `.env` mode: `mock` or `live`
- confirmation that Repo A/Wazuh data is not being restored by this process
- current database backup created successfully
- disposable restore drill passed for the selected backup
- planned maintenance window or user-impact note
- approver name and approval timestamp

Minimum evidence:

```powershell
.\scripts\backup_postgres.ps1
.\scripts\restore_drill_postgres.ps1 -BackupFile "<selected-backup.dump>"
.\scripts\report_case_retention.ps1
```

## Restore Command

Run from `soc-dashboard` only after approval:

```powershell
.\scripts\restore_postgres.ps1 -BackupFile "<selected-backup.dump>" -ConfirmRestore
```

The command overwrites the target PostgreSQL database and then runs Alembic migrations to head.

## Post-Restore Verification

Run:

```powershell
docker compose ps
curl http://localhost:8000/health
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

Also manually verify:

- superadmin login
- `/dashboard`
- `/alerts`
- one alert detail page
- `/cases` and one case detail page
- `/users`
- `/audit-logs`
- CSV export for alerts, cases, and audit logs

## Rollback If Restore Fails

If restore fails or verification fails:

1. Stop user access to the environment.
2. Preserve logs and command output.
3. Restore from the pre-restore backup created during approval.
4. Re-run migrations, smoke test, and regression tests.
5. Document the failure and the backup used for recovery.

Do not run repeated restores with different dumps without recording each attempt.

## Approval Record Template

```text
Restore request:
Target environment:
Reason:
Selected backup:
Backup timestamp:
Expected data-loss window:
Current mode:
Pre-restore backup:
Restore drill result:
Retention report result:
Approver:
Approval timestamp:
Operator:
Verifier:
Post-restore smoke result:
Post-restore regression result:
Notes:
```
