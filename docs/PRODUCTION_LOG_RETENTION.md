# Production Log Retention Policy

This policy defines how Repo B operational logs and evidence should be retained, reviewed, archived, and purged in production or production-like pilot environments.

It complements:

- [CASE_RETENTION_POLICY.md](CASE_RETENTION_POLICY.md)
- [POSTGRES_BACKUP_RESTORE.md](POSTGRES_BACKUP_RESTORE.md)
- [PRODUCTION_RESTORE_APPROVAL.md](PRODUCTION_RESTORE_APPROVAL.md)
- [PRODUCTION_SECRET_ROTATION.md](PRODUCTION_SECRET_ROTATION.md)

Repo A/Wazuh remains the source of raw security telemetry retention. This policy covers Repo B product and operations evidence.

## Data Classes

| Data | Source | Purpose |
| --- | --- | --- |
| Audit logs | PostgreSQL `audit_logs` | user, auth, and admin action evidence |
| Case history | PostgreSQL `cases`, `case_alerts`, `case_comments` | investigation workflow evidence |
| App logs | `soc-backend` and `soc-frontend` container logs | troubleshooting and incident analysis |
| Database logs | `soc-postgres` container logs | database health and restore troubleshooting |
| CI logs | GitHub Actions workflow runs | build, smoke, and regression evidence |
| PostgreSQL backups | `backups/postgres` or off-host backup storage | restore point and incident recovery |

## Retention Defaults

| Data | Dev/CI | Pilot | Production |
| --- | --- | --- | --- |
| Audit logs | 30 days | 90 days | 180 days minimum |
| Closed regression cases | 7 days | 30 days | Not expected |
| Closed pilot cases | 30 days | 90 days | Organization policy |
| Open cases | Keep | Keep | Keep |
| App/container logs | 7 days | 14 days | 30 days |
| CI logs | GitHub default | GitHub default | GitHub default or 90 days |
| Daily DB backups | 7 days | 14 days | 30 days |
| Weekly DB backups | 4 weeks | 8 weeks | 12 weeks |
| Restore approval records | Keep with handoff evidence | Keep with handoff evidence | 1 year minimum |

Production values are defaults for this project. If an organization has stricter legal, compliance, or security requirements, use the stricter policy.

## Rules

- Never purge open cases.
- Never purge audit logs to hide an operator action or failed workflow.
- Never delete backups before verifying at least one newer backup can restore successfully.
- Treat logs, backups, and exported CSV files as sensitive data.
- Keep `.env`, database dumps, and exported evidence out of git.
- Use off-host storage for production backups and long-lived evidence.

## Purge Approval

Before purging or archiving production evidence, record:

- target environment
- data class
- retention rule being applied
- date range
- expected record count or file list
- backup file used as safety point
- approver
- operator
- verification result

For pilot, the project owner can approve routine cleanup. For production, approval should come from the service owner or security lead.

## Required Cleanup Workflow

1. Generate a report before cleanup:

   ```powershell
   .\scripts\report_case_retention.ps1
   ```

2. Create a PostgreSQL backup:

   ```powershell
   .\scripts\backup_postgres.ps1
   ```

3. Verify the selected backup can restore:

   ```powershell
   .\scripts\restore_drill_postgres.ps1
   ```

4. Archive or purge only approved data.
5. Run health, smoke, and regression checks.
6. Record the cleanup result in the handoff or operations log.

## Current Implementation

Current Repo B behavior:

- audit logs are stored in PostgreSQL
- cases are retained and can be closed
- regression case cleanup is report-first and approval-based
- database backup and restore drill scripts exist
- no automated destructive log purge command exists yet

This is intentional for the pilot phase. Automated purge should be added later with dry-run mode, explicit approval, and audit records.

## Future Production Upgrade

Before production, add:

- centralized application log storage
- backup lifecycle policy for off-host storage
- audit-log archive or partition strategy
- supervised cleanup command with dry-run output
- audit record for every purge/archive action

## Retention Record Template

```text
Retention request:
Target environment:
Data class:
Date range:
Reason:
Retention rule:
Pre-cleanup backup:
Restore drill result:
Approver:
Operator:
Cleanup action:
Post-cleanup smoke result:
Post-cleanup regression result:
Notes:
```
