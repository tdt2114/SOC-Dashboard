# Production Deployment Checklist

This checklist defines the minimum release gate for deploying Repo B to a production-like or production environment.

Repo B depends on Repo A/Wazuh for alert and agent data. Production deployment must confirm both Repo B application health and Repo A integration readiness.

## Pre-Deployment

- confirm target environment and deployment window
- confirm `.env` values are for the target environment
- confirm `MOCK_MODE` is expected
- confirm Wazuh API and Indexer credentials are valid if `MOCK_MODE=false`
- confirm PostgreSQL backup exists
- confirm disposable restore drill passes
- confirm current branch and commit
- confirm GitHub Actions `Pilot Regression` is green
- confirm no unexpected local changes are included

Commands:

```powershell
git status -sb
docker compose ps
.\scripts\backup_postgres.ps1
.\scripts\restore_drill_postgres.ps1
```

## Deploy

Run:

```powershell
docker compose up -d --build
docker compose exec -T soc-backend alembic upgrade head
docker compose exec -T soc-backend python -m app.scripts.seed_initial_data
```

## Post-Deployment Verification

Run:

```powershell
.\scripts\report_runtime_health.ps1
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

Manual checks:

- superadmin login works
- `/dashboard` renders
- `/alerts` renders and opens one detail page
- `/agents` renders
- `/cases` renders and opens one case page
- `/users` is superadmin-only
- `/audit-logs` renders
- `/settings` does not expose secrets
- CSV exports work

## Production Readiness Gate

Do not call the deployment ready unless:

- backend health is `ok`
- database health is `ok`
- frontend `/login` returns HTTP 200
- smoke test passes
- regression suite passes
- backup and restore drill are current
- CI is green
- rollback plan is available
- operator has recorded deployment result

## Deployment Record Template

```text
Deployment:
Environment:
Mode:
Commit:
Operator:
Window:
Pre-deployment backup:
Restore drill:
CI result:
Runtime health:
Smoke:
Regression:
Manual checks:
Rollback needed:
Notes:
```
