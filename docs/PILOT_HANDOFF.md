# Repo B Pilot Handoff

This handoff summarizes how to run, verify, operate, and evaluate Repo B for an internal SOC pilot.

Repo B is the product layer on top of Repo A Wazuh data. Repo A remains the security core and raw telemetry source. Repo B owns users, roles, dashboard UX, analyst workflow, cases, audit logs, exports, and operational runbooks.

## Pilot Status

Repo B is pilot-ready when used with the current documented constraints:

- mock and live modes are supported
- PostgreSQL stores application data
- auth, roles, user management, audit logs, analyst workflow, cases, exports, and dashboard summary are implemented
- CI, smoke tests, and regression tests are available
- backup, restore, retention, secret rotation, monitoring, and handoff docs exist

This is not yet a fully hardened production deployment. See [ROADMAP.md](ROADMAP.md) for remaining production and platform work.

## Startup

Run from `soc-dashboard`:

```powershell
docker compose up -d --build
docker compose exec -T soc-backend alembic upgrade head
docker compose exec -T soc-backend python -m app.scripts.seed_initial_data
```

Open:

```text
http://localhost:3000
```

Use `.env`:

- `MOCK_MODE=true` for standalone Repo B validation
- `MOCK_MODE=false` for live Repo A/Wazuh integration

## Seeded Accounts

Seeded account values come from `.env` or `.env.ci`.

| Account | Purpose |
| --- | --- |
| `SEED_SUPERADMIN_USERNAME` | full access, user management, audit logs, settings |
| `SEED_ADMIN_USERNAME` | admin role seed |
| `SEED_VIEWER_USERNAME` | read-only role regression |
| `SEED_ANALYST_USERNAME` | analyst workflow regression |
| `SEED_ROLE_ADMIN_USERNAME` | non-superuser admin role regression |

Change default seed passwords outside local development.

## Page Guide

| Page | Purpose | Primary Roles |
| --- | --- | --- |
| `/login` | authenticate users | all users |
| `/dashboard` | 24h operations summary | viewer, analyst, admin, superadmin |
| `/alerts` | search, filter, paginate, export, and triage alerts | viewer, analyst, admin, superadmin |
| `/alerts/[id]` | inspect normalized alert detail and raw payload | viewer, analyst, admin, superadmin |
| `/agents` | monitor Wazuh agent inventory | viewer, analyst, admin, superadmin |
| `/agents/[id]` | inspect one agent | viewer, analyst, admin, superadmin |
| `/cases` | list and create investigation cases | analyst, admin, superadmin |
| `/cases/[id]` | case detail, comments, alert links, status | analyst, admin, superadmin |
| `/users` | user and role management | superadmin |
| `/audit-logs` | review auth and admin activity | superadmin |
| `/settings` | read-only operational settings | superadmin |
| `/profile` | change own password | authenticated users |

Backend permissions remain the security boundary. Frontend role-based UX is support for usability, not the only protection.

## Verification Commands

Runtime health:

```powershell
.\scripts\report_runtime_health.ps1
```

Smoke:

```powershell
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
```

Regression:

```powershell
$env:PILOT_TEST_USERNAME = "<superadmin-username>"
$env:PILOT_TEST_PASSWORD = "<superadmin-password>"
python -m unittest discover -s tests -v
```

Backup:

```powershell
.\scripts\backup_postgres.ps1
.\scripts\restore_drill_postgres.ps1
```

Retention report:

```powershell
.\scripts\report_case_retention.ps1
```

## Evidence Files

- [PILOT_TEST_RESULTS.md](PILOT_TEST_RESULTS.md)
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md)
- [PILOT_READINESS.md](PILOT_READINESS.md)
- [POSTGRES_BACKUP_RESTORE.md](POSTGRES_BACKUP_RESTORE.md)
- [CASE_RETENTION_POLICY.md](CASE_RETENTION_POLICY.md)
- [PRODUCTION_MONITORING.md](PRODUCTION_MONITORING.md)
- [PRODUCTION_LOG_RETENTION.md](PRODUCTION_LOG_RETENTION.md)
- [PRODUCTION_SECRET_ROTATION.md](PRODUCTION_SECRET_ROTATION.md)
- [PRODUCTION_RESTORE_APPROVAL.md](PRODUCTION_RESTORE_APPROVAL.md)
- [ROADMAP.md](ROADMAP.md)

## Handoff Checklist

- stack starts successfully
- backend `/health` is `ok`
- frontend `/login` returns HTTP 200
- seed accounts exist
- superadmin can log in
- role access checks pass
- smoke test passes
- regression tests pass
- GitHub Actions `Pilot Regression` passes
- live mode has been verified with Repo A before external pilot use
- backup and restore drill pass
- retention, restore approval, secret rotation, and monitoring docs are available

## Known Production Gaps

- no SSO
- no external notification channel
- no rate limiting
- no Redis/session store split
- no centralized production log sink configured yet
- no worker/background job service
- no SOAR or destructive active response
- no AI or external enrichment

These gaps do not block an internal pilot, but they should be addressed before production-grade use.
