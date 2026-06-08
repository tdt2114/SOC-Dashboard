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

Local font strategy verification:

```text
Removed frontend next/font/google usage.
Frontend font stack now uses Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif.

docker compose build soc-frontend
Compiled successfully

python -m unittest discover -s tests -v
Ran 13 tests in 5.157s
OK

python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (live)
PASS: frontend login succeeds
PASS: /alerts renders
PASS: alert detail renders with back action
PASS: /api/exports/alerts.csv exports CSV
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

- Add CI to run smoke and pilot regression tests automatically.

## 2026-06-08

Environment:

- Mode: mock
- Stack: Docker Compose
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

Dependency/build review:

```text
npm audit --json
vulnerabilities: 0 total

npm ls next react react-dom postcss
next@16.2.7
react@19.2.7
react-dom@19.2.7
postcss@8.5.15

docker compose build soc-frontend
Image soc-dashboard-soc-frontend Built
```

Build hardening completed:

- Added `frontend/package-lock.json`.
- Switched frontend Docker install step from `npm install` to `npm ci`.
- Migrated Next.js route handlers and dynamic pages for async `params`.
- Migrated server cookie reads to async `cookies()`.
- Replaced deprecated `middleware.ts` convention with `proxy.ts`.

Latest automated results:

```text
python -m unittest discover -s tests -v
Ran 13 tests in 2.540s
OK

python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (mock)
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

Current remaining operational work:

- Re-run live mode verification with Repo A before handoff if the stack is switched from mock mode back to live mode.

CI workflow added:

```text
.github/workflows/pilot-regression.yml
```

The workflow runs frontend audit, Docker Compose build/start, migrations, seed, smoke test, and pilot regression tests in mock mode using `.env.ci`.

Local post-CI-workflow verification:

```text
docker compose up -d --build
docker compose exec -T soc-backend alembic upgrade head
docker compose exec -T soc-backend python -m app.scripts.seed_initial_data
python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (mock)
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

python -m unittest discover -s tests -v
Ran 13 tests in 2.595s
OK
```

Remote GitHub Actions verification:

```text
Workflow: Pilot Regression #1
Trigger: push
Branch: main
Commit: 3e41d37
Status: Success
Total duration: 1m 15s
Job: pilot-regression
Job duration: 1m 10s
```

The run completed successfully on GitHub Actions. The run also reported a warning that some GitHub Actions are using the deprecated Node.js 20 action runtime. This is not a test failure, but the workflow actions should be reviewed in the next operational hardening pass.

GitHub Actions runtime warning follow-up:

```text
Updated .github/workflows/pilot-regression.yml:
actions/checkout@v4 -> actions/checkout@v6
actions/setup-python@v5 -> actions/setup-python@v6
actions/setup-node@v4 -> actions/setup-node@v6
```

These versions target the newer Node.js action runtime. Re-run GitHub Actions after pushing this change to confirm the warning is cleared.

Current remaining operational work:

- Re-run live mode verification with Repo A before handoff if the stack is switched from mock mode back to live mode.
- Add centralized production monitoring and log shipping.

Case retention policy added:

```text
docs/CASE_RETENTION_POLICY.md
scripts/report_case_retention.ps1
```

The script is read-only and reports case counts plus closed regression/pilot cases past the configured retention windows. It does not delete or archive data.

Local retention report verification:

```text
.\scripts\report_case_retention.ps1
Case retention report
Database: soc_dashboard
Regression retention days: 30
Pilot retention days: 90

Cases by status:
closed | 17
open   | 1

Closed regression cases past retention: 0
Closed pilot cases past retention: 0
Report only. No data was changed.
```

Post-retention-policy verification:

```text
python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (mock)
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

python -m unittest discover -s tests -v
Ran 13 tests in 2.329s
OK
```

Production restore approval procedure added:

```text
docs/PRODUCTION_RESTORE_APPROVAL.md
docs/POSTGRES_BACKUP_RESTORE.md links the approval procedure before destructive restore.
docs/PILOT_READINESS.md links the approval procedure for production-like restore operations.
```

No runtime code changed in this step.

Production secret rotation procedure added on `main`:

```text
docs/PRODUCTION_SECRET_ROTATION.md
README.md and docs/PILOT_READINESS.md link the procedure for production-like credential changes.
```

Production log retention policy added:

```text
docs/PRODUCTION_LOG_RETENTION.md
README.md and docs/PILOT_READINESS.md link the policy for log, audit evidence, backup, and cleanup retention.
```

Post-policy and workflow-runtime local verification:

```text
git diff --check
OK

npm audit --audit-level=moderate
found 0 vulnerabilities

python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
PASS: backend health ok (mock)
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

python -m unittest discover -s tests -v
Ran 13 tests in 2.106s
OK
```

No runtime application code changed in this step.
