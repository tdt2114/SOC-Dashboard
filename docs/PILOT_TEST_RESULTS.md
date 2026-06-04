# Repo B Pilot Test Results

This file captures verification results that can be reused for pilot reports and handoff notes.

## 2026-06-04

Environment:

- Mode: live
- Stack: Docker Compose
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

Completed checks:

- Production frontend container runs with `next start`.
- Stale auth cookie redirects to `/login` without a redirect loop.
- `/alerts` uses compact saved search UI and agent dropdown.
- Alert detail keeps `Back to alerts` and raw JSON.
- Backend role boundaries are checked for viewer, analyst, non-superuser admin, and superadmin.
- Case workflow regression covers create, alert link, comment, update, alert unlink, and close.
- Frontend proxy regression covers saved search and case workflow.

Latest automated results:

```text
python -m unittest discover -s tests -v
Ran 13 tests ... OK

python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (live)
PASS: login page renders
PASS: stale cookie redirects to login
PASS: frontend login succeeds
PASS: /dashboard renders
PASS: /alerts renders
PASS: alert detail renders with back action
PASS: /cases renders
PASS: /users renders
PASS: /audit-logs renders
PASS: /settings renders
PASS: /api/exports/alerts.csv exports CSV
PASS: /api/exports/cases.csv exports CSV
PASS: /api/exports/audit-logs.csv exports CSV
```

Post-restore-drill verification:

```text
python -m unittest discover -s tests -v
Ran 13 tests in 4.669s
OK

python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (live)
PASS: login page renders
PASS: stale cookie redirects to login
PASS: frontend login succeeds
PASS: /dashboard renders
PASS: /alerts renders
PASS: alert detail renders with back action
PASS: /cases renders
PASS: /users renders
PASS: /audit-logs renders
PASS: /settings renders
PASS: /api/exports/alerts.csv exports CSV
PASS: /api/exports/cases.csv exports CSV
PASS: /api/exports/audit-logs.csv exports CSV
```

Backup verification:

```text
.\scripts\backup_postgres.ps1
Backup created: D:\money\SOC-Wazuh\soc-dashboard\backups\postgres\soc-dashboard-soc_dashboard-20260604-162938.dump
Database: soc_dashboard
Size bytes: 55730

pg_restore --list /tmp/soc-dashboard-verify.dump
Archive created at 2026-06-04 09:29:39 UTC
dbname: soc_dashboard
TOC Entries: 148
Format: CUSTOM
Compression: gzip

.\scripts\restore_drill_postgres.ps1
Restore drill OK
Backup file: D:\money\SOC-Wazuh\soc-dashboard\backups\postgres\soc-dashboard-soc_dashboard-20260604-162938.dump
Database: soc_restore_drill
Public tables: 15
Alembic rows: 1
Users: 5
Cases: 4
Disposable restore drill container removed: soc-postgres-restore-drill-20260604-163318
```

Issues found and fixed:

- Alert detail layout overflow was fixed.
- Dashboard/alert agent display now maps manager agent `000` to `Wazuh Manager`.
- Alerts page pagination now supports 10 or 15 rows per page.
- Saved search UI was compacted into the alert filter panel.
- Stale case response after mutating case alerts/comments was fixed with refreshed SQLAlchemy loading.

Known remaining operational work:

- Replace remote font dependency with a local font strategy if offline builds are required.
- Review frontend dependency advisories.
- Add CI to run smoke and pilot regression tests automatically.
