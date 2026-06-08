# Production Secret Rotation Procedure

This procedure defines how to rotate Repo B secrets in production or production-like pilot environments without losing access to the application.

Repo B owns application credentials and integration credentials. Repo A/Wazuh remains the source of Wazuh service accounts and security telemetry.

## Secrets In Scope

| Secret | Purpose | Rotation Trigger |
| --- | --- | --- |
| `JWT_SECRET_KEY` | signs access and refresh tokens | scheduled rotation, suspected leak |
| `POSTGRES_PASSWORD` | PostgreSQL application database password | scheduled rotation, operator change, suspected leak |
| `SEED_ADMIN_PASSWORD` | bootstrap admin password | before handoff, suspected leak |
| `SEED_SUPERADMIN_PASSWORD` | bootstrap superadmin password | before handoff, suspected leak |
| `WAZUH_API_PASSWORD` | reads agents and Wazuh API data | Repo A service-account rotation |
| `WAZUH_INDEXER_PASSWORD` | reads alerts from Wazuh Indexer | Repo A service-account rotation |

Never commit `.env`, database dumps, generated tokens, or real credentials.

## Rotation Cadence

For pilot:

- rotate seed admin and superadmin passwords before handoff
- rotate Wazuh integration credentials whenever Repo A service accounts change
- rotate database and JWT secrets after suspected exposure

For production:

- rotate admin/bootstrap passwords at every operator handoff
- rotate integration credentials according to Repo A policy
- rotate database credentials on a defined maintenance cadence
- rotate JWT secret during a maintenance window because active sessions will be invalidated

## Pre-Rotation Checklist

Before changing secrets:

1. Confirm the target environment and maintenance window.
2. Create a PostgreSQL backup:

   ```powershell
   .\scripts\backup_postgres.ps1
   ```

3. Run the retention report:

   ```powershell
   .\scripts\report_case_retention.ps1
   ```

4. Confirm a rollback value exists for each secret being changed.
5. Confirm at least one superadmin can log in after the planned change.
6. For Wazuh credentials, confirm the replacement service account works in Repo A before updating Repo B.

## Rotation Order

Use the narrowest change possible.

1. Rotate Wazuh integration credentials first if only Repo A credentials changed.
2. Rotate seed/admin passwords before user handoff.
3. Rotate `JWT_SECRET_KEY` only during a maintenance window.
4. Rotate `POSTGRES_PASSWORD` last because it affects database connectivity and may require database-user updates outside `.env`.

## Apply Changes

Update the deployment secret source first. For local Docker Compose, that is `.env`.

Then restart services:

```powershell
docker compose up -d --build
docker compose exec -T soc-backend alembic upgrade head
docker compose exec -T soc-backend python -m app.scripts.seed_initial_data
```

If only frontend-safe settings changed, a full rebuild may not be required. For credential changes, use the full restart path above.

## Verification

Run:

```powershell
docker compose ps
curl http://localhost:8000/health
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

Manual checks:

- superadmin login works
- stale sessions redirect to `/login`
- `/dashboard`, `/alerts`, `/agents`, `/cases`, `/users`, `/audit-logs`, and `/settings` render for the correct roles
- live mode can still read Wazuh alerts and agents if `MOCK_MODE=false`

## Rollback

If verification fails:

1. Restore the previous secret values in the deployment secret source.
2. Restart services.
3. Run health, smoke, and regression checks again.
4. Document which secret failed and whether any user sessions were invalidated.

If database access is broken after rotating `POSTGRES_PASSWORD`, roll back both the database user password and the `.env` value before restarting.

## Rotation Record Template

```text
Rotation request:
Target environment:
Secrets rotated:
Reason:
Maintenance window:
Pre-rotation backup:
Retention report result:
Operator:
Approver:
Applied at:
Post-rotation health result:
Post-rotation smoke result:
Post-rotation regression result:
Rollback needed:
Notes:
```
