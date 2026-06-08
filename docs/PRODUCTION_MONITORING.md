# Production Monitoring and Log Shipping Runbook

This runbook defines the minimum monitoring and log-shipping expectations for Repo B production or production-like pilot environments.

Repo B is the product and workflow layer. Repo A/Wazuh remains the security telemetry source. Monitoring Repo B means tracking application availability, database health, workflow evidence, CI health, and operational logs.

## Monitoring Scope

| Target | Signal | Expected State |
| --- | --- | --- |
| Backend | `GET /health` | HTTP 200, `status=ok`, `database=ok` |
| Frontend | `GET /login` | HTTP 200 |
| PostgreSQL | Docker health status | `healthy` |
| Auth/session | smoke test stale-cookie check | redirects to `/login` without loop |
| Alert data | smoke test `/alerts` and alert detail | renders rows and detail |
| Case workflow | regression tests | create/link/comment/update/close works |
| CI | GitHub Actions `Pilot Regression` | success on push/PR |
| Backups | backup and restore drill | backup exists and disposable restore passes |

## Local Health Report

For pilot and local operations, run:

```powershell
.\scripts\report_runtime_health.ps1
```

The script is read-only. It checks Docker Compose status, backend health, frontend login reachability, and the latest container log tails.

Use this report before handoff, after restarts, after restore, and after credential rotation.

## Minimum Alert Conditions

Create operational alerts for:

- backend `/health` fails or returns `database` not `ok`
- frontend `/login` does not return HTTP 200
- `soc-postgres` is not healthy
- `soc-backend` or `soc-frontend` container is not running
- GitHub Actions `Pilot Regression` fails
- backup creation fails
- restore drill fails
- smoke test fails after deploy, restore, or secret rotation

For pilot, these can be manual checks recorded in the handoff notes. For production, wire these into a monitoring system.

## Log Sources

Collect logs from:

- `soc-backend`
- `soc-frontend`
- `soc-postgres`
- GitHub Actions workflow runs
- backup and restore scripts
- smoke and regression test outputs

Treat logs as sensitive. They can include usernames, URLs, case metadata, operational timing, and exported evidence paths.

## Recommended Shipping Options

Choose one path before production:

| Option | Use When | Notes |
| --- | --- | --- |
| Wazuh/Indexer | keep SOC evidence in the existing Repo A stack | aligns with the project domain |
| Loki/Grafana | need lightweight app-log dashboards | good for service health and container logs |
| ELK/OpenSearch | need broader log analytics | heavier operations footprint |
| Docker log retention only | pilot or local-only validation | acceptable temporarily, not production-grade |

For the current pilot, Docker log retention plus explicit smoke/regression reports is acceptable. For production, use centralized shipping.

## Daily Pilot Check

Run:

```powershell
.\scripts\report_runtime_health.ps1
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
```

Review:

- backend mode is expected: `mock` or `live`
- database is `ok`
- frontend responds
- smoke test passes
- no unexpected container restarts

## Post-Incident Check

After outage, failed deploy, restore, or secret rotation:

1. Run the runtime health report.
2. Run smoke test.
3. Run pilot regression tests.
4. Export or save relevant logs outside git.
5. Record the incident result in the operations handoff notes.

Commands:

```powershell
.\scripts\report_runtime_health.ps1
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

## Future Production Upgrade

Before production, add:

- centralized log sink configuration
- retention policy in the chosen log platform
- uptime checks for frontend and backend
- database-health alert
- CI failure notification
- backup and restore-drill notification
- dashboard for service status and recent incidents

## Monitoring Record Template

```text
Monitoring check:
Target environment:
Mode:
Backend health:
Frontend health:
Postgres health:
Smoke result:
Regression result:
CI result:
Backup/restore drill result:
Log sink:
Issues found:
Operator:
Timestamp:
Notes:
```
