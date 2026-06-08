# Case Retention and Archival Policy

This policy covers pilot and regression case data in Repo B. It is meant for internal pilot operations, not as a final legal or compliance retention policy.

## Scope

Repo B stores case workflow data in PostgreSQL:

- `cases`
- `case_alerts`
- `case_comments`

Repo A remains the source of security telemetry and raw alert data. Repo B case retention only affects product workflow records, not Wazuh alert retention.

## Case Classes

Use clear naming so pilot reports and cleanup checks can separate real investigation data from generated test data.

| Class | Identifier | Retention Target |
| --- | --- | --- |
| Regression case | Title starts with `pilot-api-case-regression-` or `pilot-ui-case-regression-` | Short-lived test evidence |
| Pilot case | Human-created pilot investigation case | Keep for pilot review |
| Production case | Real operational investigation after pilot | Governed by production policy |

Regression tests close their generated cases instead of deleting them. This preserves auditability while keeping the cleanup decision explicit.

## Retention Defaults

| Data | Dev/CI | Pilot | Production |
| --- | --- | --- | --- |
| Closed regression cases | 7 days | 30 days | Not expected |
| Closed pilot cases | 30 days | 90 days | Organization policy |
| Open cases | Keep | Keep | Keep |
| Audit logs | Keep for pilot evidence | Keep for pilot evidence | Organization policy |

Do not hard-delete open cases. Closed case cleanup must only happen after a successful PostgreSQL backup and a review of the report output.

## Current Implementation

Current app behavior:

- Cases can be closed through the existing case update flow.
- There is no hard-delete endpoint for cases.
- Regression tests create, mutate, unlink, and close their own cases.
- Cleanup is operational: report first, backup second, delete or archive later only with explicit approval.

This is intentional for the pilot phase. It avoids accidental loss of investigation history while still making stale test data visible.

## Required Pilot Workflow

Before a pilot handoff, demo, database migration, or cleanup window:

1. Run the retention report:

   ```powershell
   .\scripts\report_case_retention.ps1
   ```

2. Create a PostgreSQL backup:

   ```powershell
   .\scripts\backup_postgres.ps1
   ```

3. Verify restore into a disposable database:

   ```powershell
   .\scripts\restore_drill_postgres.ps1
   ```

4. Review closed regression cases and decide whether to keep them as test evidence or remove/archive them through an approved maintenance change.

## Future Production Upgrade

Before production, add one of these explicit mechanisms:

- `archived_at` and `archived_by_user_id` columns on `cases`
- a dedicated case archive table
- a supervised admin cleanup command with dry-run and audit output

Any cleanup command must support dry-run mode, require superadmin approval, and write an audit record.
