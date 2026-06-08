# Repo B Pilot Readiness

This checklist is for running Repo B as an internal pilot, not as a fully hardened production deployment.

## What Is Ready

- Frontend runs in production mode with `next start`.
- Backend and frontend are containerized through Docker Compose.
- PostgreSQL stores application data.
- Auth, users, roles, audit logs, analyst workflow, cases, dashboard summary, settings, and exports are implemented.
- Stale auth cookies are handled by middleware and redirect back to login instead of causing a redirect loop.
- Mock mode and live mode are both supported.
- Pilot handoff, feature matrix, and roadmap docs are available:
  - [PILOT_HANDOFF.md](PILOT_HANDOFF.md)
  - [FEATURE_MATRIX.md](FEATURE_MATRIX.md)
  - [ROADMAP.md](ROADMAP.md)
- Deployment, rollback, and log sink decision docs are available:
  - [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)
  - [RELEASE_ROLLBACK_CHECKLIST.md](RELEASE_ROLLBACK_CHECKLIST.md)
  - [LOG_SINK_DECISION.md](LOG_SINK_DECISION.md)

## Required Startup Checks

Run:

```bash
docker compose up -d --build
docker compose exec soc-backend alembic upgrade head
docker compose exec soc-backend python -m app.scripts.seed_initial_data
```

Check containers:

```bash
docker compose ps
```

Expected:

- `soc-postgres` healthy
- `soc-backend` up
- `soc-frontend` up

Check backend:

```bash
curl http://localhost:8000/health
```

Expected:

- `status` is `ok`
- `database` is `ok`
- `mode` is the expected `mock` or `live`

Check frontend:

```bash
curl -I http://localhost:3000/login
```

Expected: HTTP `200`.

## Backup Requirement

Before a pilot handoff, demo, migration, or bulk account change, create a PostgreSQL backup:

```powershell
.\scripts\backup_postgres.ps1
```

See [POSTGRES_BACKUP_RESTORE.md](POSTGRES_BACKUP_RESTORE.md) for backup, restore, retention, and verification steps.

Verify the backup can restore into a disposable PostgreSQL container:

```powershell
.\scripts\restore_drill_postgres.ps1
```

For production-like restore operations, complete [PRODUCTION_RESTORE_APPROVAL.md](PRODUCTION_RESTORE_APPROVAL.md) before running `restore_postgres.ps1 -ConfirmRestore`.

For production-like credential changes, follow [PRODUCTION_SECRET_ROTATION.md](PRODUCTION_SECRET_ROTATION.md) and record the verification result.

## Retention Requirement

Before a pilot handoff or cleanup window, run the read-only case retention report:

```powershell
.\scripts\report_case_retention.ps1
```

See [CASE_RETENTION_POLICY.md](CASE_RETENTION_POLICY.md) for regression case, pilot case, and future production retention rules.

For production-like log, backup, and audit evidence retention, follow [PRODUCTION_LOG_RETENTION.md](PRODUCTION_LOG_RETENTION.md).

For production-like service monitoring and log shipping, follow [PRODUCTION_MONITORING.md](PRODUCTION_MONITORING.md).

For production-like deployment, release, rollback, and log-sink decisions, use:

- [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- [RELEASE_ROLLBACK_CHECKLIST.md](RELEASE_ROLLBACK_CHECKLIST.md)
- [LOG_SINK_DECISION.md](LOG_SINK_DECISION.md)

Run a local health report after startup, restore, credential rotation, or deployment:

```powershell
.\scripts\report_runtime_health.ps1
```

## Manual Smoke Test

Use the seeded superadmin account from `.env`.

1. Log in at `http://localhost:3000/login`.
2. Open `/dashboard`.
3. Open `/alerts` and verify alert rows render.
4. Open one alert detail page.
5. Bookmark the alert.
6. Assign the alert to an analyst/admin user.
7. Add a note.
8. Create a case from the alert or from `/cases`.
9. Add a comment to the case.
10. Open `/users` and verify superadmin-only access.
11. Open `/audit-logs` and verify login/user actions are visible.
12. Open `/settings` and verify secrets are not shown.
13. Export alerts, cases, and audit logs as CSV.

## Automated Smoke Test

The repo includes a dependency-free Python smoke script:

```bash
python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
```

Or use environment variables:

```bash
SMOKE_SUPERADMIN_USERNAME=<username> SMOKE_SUPERADMIN_PASSWORD=<password> python scripts/smoke_pilot.py
```

It checks:

- backend `/health`
- frontend `/login`
- stale-cookie redirect behavior
- authenticated dashboard, alerts, cases, users, audit logs, settings
- alerts pagination summary and next action
- alert detail back action and raw JSON section
- CSV exports for alerts, cases, and audit logs

Role checks:

- Admin or analyst can access cases.
- Admin or analyst cannot access `/users`, `/audit-logs`, or `/settings`.
- Viewer can monitor alerts/agents but cannot use analyst workflow.

## Pilot Regression Tests

Run the dependency-free unittest suite before pilot handoff and after changes to auth, navigation, alerts, saved searches, or workflow.

PowerShell:

```powershell
$env:PILOT_TEST_USERNAME = "<superadmin-username>"
$env:PILOT_TEST_PASSWORD = "<superadmin-password>"
python -m unittest discover -s tests -v
```

Bash:

```bash
PILOT_TEST_USERNAME=<username> PILOT_TEST_PASSWORD=<password> python -m unittest discover -s tests -v
```

The suite covers:

- API: health, auth, users gate, alerts, agents, filters, saved-search CRUD, bookmark, and assignment
- Case workflow: create, link alert, comment, update, unlink alert, and close regression case
- Role permissions: seeded viewer, analyst, and non-superuser admin access boundaries
- Frontend: stale-cookie redirect, protected routes, alert detail back action, alert pagination, compact saved-search UI, agent dropdown, role navigation/access states, saved-search proxy cleanup, and case proxy workflow

## CI

GitHub Actions workflow:

```text
.github/workflows/pilot-regression.yml
```

The workflow runs in mock mode using `.env.ci`, starts Docker Compose from a clean CI volume, applies migrations, seeds CI users, runs frontend audit, smoke checks, and the pilot regression suite.

## Known Gaps Before Production

- No SSO.
- No external notification channel.
- No rate limiting.
- No Redis/session store split.
- No centralized production log sink yet.
- Frontend dependency advisories were reviewed on 2026-06-08; `npm audit` currently reports 0 vulnerabilities.
- Frontend now uses a system font stack and does not depend on Google Fonts during Docker build.

## Pilot Exit Criteria

The pilot can be considered successful when:

- Operators can log in and reach the correct screens for their roles.
- Live alerts and agents load reliably from Repo A.
- Analyst workflow is usable from alert triage to case comment.
- Superadmin can manage users without direct database access.
- Audit logs capture auth and account-management actions.
- CSV export works for the expected investigation handoff.
- No redirect loop or blank page appears during expired-session handling.

## Recommended Next Work

1. Re-run live mode verification with Repo A before external pilot handoff if `.env` is switched back from mock mode.
2. Prepare final presentation or report material from the handoff package and test evidence.
3. Implement centralized log shipping after pilot approval.
