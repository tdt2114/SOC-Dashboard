# soc-dashboard

Repo B is the product layer on top of Repo A Wazuh data. It keeps detection and raw security data in Repo A, while Repo B owns the dashboard, user management, analyst workflow, audit trail, cases, exports, and operational UX.

## Current Scope

Implemented:

- Alert list and alert detail from Wazuh Indexer
- Agent inventory and agent detail from Wazuh API
- Mock mode for standalone Repo B testing
- Live mode for Repo A integration
- PostgreSQL app database
- Alembic migrations
- Internal auth with access and refresh tokens
- Role model: `viewer`, `analyst`, `admin`, `superadmin`
- User management for superadmin
- Profile password change
- Audit logs
- Saved searches
- Alert bookmark, assignment, notes, and in-app notifications
- Case list/detail, case comments, and alert-to-case linking
- Dashboard summary
- Read-only settings page
- CSV exports
- Loading, empty, error, and access-denied states

Intentionally not included in this phase:

- AI enrichment
- SOAR or destructive active response
- Slack, Telegram, or email delivery
- VirusTotal or external enrichment
- SSO
- Mobile-specific UI

## Architecture

```text
User
  |
  v
Next.js frontend
  |
  v
FastAPI backend
  |
  +-- PostgreSQL
  |     users, roles, refresh tokens, workflow data, audit logs, cases
  |
  +-- Wazuh Indexer
  |     alerts and search data
  |
  +-- Wazuh API
        agent inventory and metadata
```

## Local Startup

1. Copy `.env.example` to `.env` if needed.
2. Set `MOCK_MODE=true` for standalone testing, or `MOCK_MODE=false` for live Repo A integration.
3. Start the stack:

```bash
docker compose up --build
```

4. Apply migrations if the database is new:

```bash
docker compose exec soc-backend alembic upgrade head
```

5. Seed initial accounts:

```bash
docker compose exec soc-backend python -m app.scripts.seed_initial_data
```

6. Open:

```text
http://localhost:3000
```

The frontend Docker image runs `next build` during image build and starts with `next start`.

## Health Checks

Backend:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","mode":"mock-or-live","database":"ok"}
```

Frontend:

```bash
curl -I http://localhost:3000/login
```

Expected: HTTP `200`.

## Automated Smoke Test

Run a pilot smoke test after the stack is up:

```bash
python scripts/smoke_pilot.py --username <superadmin-username> --password <superadmin-password>
```

The script verifies:

- backend health
- login page
- stale-cookie redirect behavior
- authenticated dashboard, alerts, cases, users, audit logs, and settings
- alerts pagination summary and next action
- alert detail back action
- CSV exports

## Pilot Regression Tests

Run the deeper API and frontend route regression tests before pilot handoff or after changing auth, alerts, saved searches, workflow, or navigation.

PowerShell:

```powershell
$env:PILOT_TEST_USERNAME = "<superadmin-username>"
$env:PILOT_TEST_PASSWORD = "<superadmin-password>"
python -m unittest discover -s tests -v
```

Bash:

```bash
PILOT_TEST_USERNAME=<superadmin-username> PILOT_TEST_PASSWORD=<superadmin-password> python -m unittest discover -s tests -v
```

The tests verify:

- backend health, auth `/me`, and superadmin-only user API access
- alert list pagination, severity filter, agent list, agent-name filter, and alert detail
- saved search create/update/delete with cleanup
- alert bookmark and assignment flows with cleanup
- case create, alert link, comment, update, alert unlink, and close flow
- frontend stale-cookie redirect behavior
- protected frontend routes
- `/alerts` compact saved search UI, agent dropdown, pagination, and alert detail back action
- frontend saved-search proxy create/delete flow with cleanup
- frontend case proxy workflow with closed-case cleanup

## Backup and Results

- PostgreSQL backup/restore runbook: [docs/POSTGRES_BACKUP_RESTORE.md](docs/POSTGRES_BACKUP_RESTORE.md)
- Pilot verification results for report reuse: [docs/PILOT_TEST_RESULTS.md](docs/PILOT_TEST_RESULTS.md)

## Seeded Accounts

The seed script creates:

- default department
- roles: `admin`, `analyst`, `viewer`
- one admin account
- one superadmin account
- pilot regression accounts for `viewer`, `analyst`, and non-superuser `admin`

Credential values come from `.env`:

- `SEED_ADMIN_USERNAME`
- `SEED_ADMIN_PASSWORD`
- `SEED_SUPERADMIN_USERNAME`
- `SEED_SUPERADMIN_PASSWORD`
- `SEED_VIEWER_USERNAME`
- `SEED_VIEWER_PASSWORD`
- `SEED_ANALYST_USERNAME`
- `SEED_ANALYST_PASSWORD`
- `SEED_ROLE_ADMIN_USERNAME`
- `SEED_ROLE_ADMIN_PASSWORD`

Change these values outside local development.

## Main Routes

- `/login`
- `/dashboard`
- `/alerts`
- `/alerts/[id]`
- `/agents`
- `/agents/[id]`
- `/cases`
- `/cases/[id]`
- `/users`
- `/audit-logs`
- `/settings`
- `/profile`

## Role Behavior

- `viewer`: dashboard, alerts, agents
- `analyst`: viewer access plus saved searches, bookmarks, assignments, notes, cases
- `admin`: analyst workflow access
- `superadmin`: all admin screens, user management, audit logs, settings

Backend endpoints still enforce permissions. Frontend access-denied states are UX support, not the security boundary.

The pilot regression suite logs in as the seeded viewer, analyst, and non-superuser admin accounts to verify both backend permissions and frontend navigation/access states.

## Pilot Readiness

See [docs/PILOT_READINESS.md](docs/PILOT_READINESS.md).
