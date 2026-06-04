# Repo B Pilot Readiness

This checklist is for running Repo B as an internal pilot, not as a fully hardened production deployment.

## What Is Ready

- Frontend runs in production mode with `next start`.
- Backend and frontend are containerized through Docker Compose.
- PostgreSQL stores application data.
- Auth, users, roles, audit logs, analyst workflow, cases, dashboard summary, settings, and exports are implemented.
- Stale auth cookies are handled by middleware and redirect back to login instead of causing a redirect loop.
- Mock mode and live mode are both supported.

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
- CSV exports for alerts, cases, and audit logs

Role checks:

- Admin or analyst can access cases.
- Admin or analyst cannot access `/users`, `/audit-logs`, or `/settings`.
- Viewer can monitor alerts/agents but cannot use analyst workflow.

## Known Gaps Before Production

- No automated E2E test suite yet.
- API test coverage should be expanded for auth, roles, users, cases, and exports.
- No SSO.
- No external notification channel.
- No rate limiting.
- No Redis/session store split.
- No backup/restore runbook for PostgreSQL.
- No log retention policy.
- No formal secret rotation procedure.
- Frontend dependencies should be reviewed because `npm audit` currently reports one moderate and one high advisory during image build.
- Next font build may retry Google Fonts during Docker build; consider local font bundling if builds must work fully offline.

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

1. Add backend API tests for auth, users, cases, and exports.
2. Add frontend E2E smoke tests for login, alerts, cases, users, audit logs, and stale-cookie behavior.
3. Add PostgreSQL backup/restore notes.
4. Replace remote Google font dependency with a local font strategy.
5. Review and address npm advisories.
