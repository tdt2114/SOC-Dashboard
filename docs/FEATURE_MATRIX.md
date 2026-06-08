# Repo B Feature Matrix

This matrix maps the current Repo B product surface to pilot readiness, verification evidence, and future work.

| Area | Feature | Status | Evidence |
| --- | --- | --- | --- |
| Data mode | Mock mode | Pilot-ready | smoke and regression tests |
| Data mode | Live Repo A/Wazuh mode | Pilot-ready | live smoke/regression recorded in `PILOT_TEST_RESULTS.md` |
| Auth | login, logout, refresh, current user | Pilot-ready | smoke and API regression |
| Auth | stale-cookie redirect handling | Pilot-ready | frontend regression |
| Roles | viewer, analyst, admin, superadmin | Pilot-ready | role regression tests |
| Users | list, create, edit, reset password, active state | Pilot-ready | superadmin UI/API regression |
| Profile | own password change | Pilot-ready | implemented and manually verified |
| Dashboard | 24h operations summary | Pilot-ready | smoke route check |
| Alerts | list, search, severity, rule, time filters | Pilot-ready | API and frontend regression |
| Alerts | pagination 10/15 rows | Pilot-ready | frontend regression |
| Alerts | agent dropdown filter | Pilot-ready | frontend regression |
| Alerts | detail page with back action and raw JSON | Pilot-ready | frontend regression |
| Alerts | CSV export | Pilot-ready | smoke export check |
| Agents | list and detail | Pilot-ready | API/frontend checks |
| Workflow | saved searches | Pilot-ready | API and frontend proxy regression |
| Workflow | bookmarks | Pilot-ready | API regression |
| Workflow | assignment | Pilot-ready | API regression |
| Workflow | notes | Pilot-ready | detail workflow support |
| Notifications | in-app assignment notifications | Pilot-ready | implemented workflow support |
| Cases | list, create, detail, update status | Pilot-ready | case workflow regression |
| Cases | link/unlink alerts | Pilot-ready | case workflow regression |
| Cases | comments | Pilot-ready | case workflow regression |
| Audit | audit log records and viewer | Pilot-ready | smoke route and backend coverage |
| Settings | read-only operational settings | Pilot-ready | smoke route check |
| CI | GitHub Actions pilot regression | Pilot-ready | `Pilot Regression #3` success |
| Testing | smoke script | Pilot-ready | `scripts/smoke_pilot.py` |
| Testing | API/frontend regression suite | Pilot-ready | `python -m unittest discover -s tests -v` |
| Backup | PostgreSQL backup script | Pilot-ready | backup verification recorded |
| Restore | disposable restore drill | Pilot-ready | restore drill recorded |
| Retention | case retention report | Pilot-ready | `scripts/report_case_retention.ps1` |
| Operations | runtime health report | Pilot-ready | `scripts/report_runtime_health.ps1` |
| Operations | restore approval procedure | Pilot-ready | `PRODUCTION_RESTORE_APPROVAL.md` |
| Operations | secret rotation procedure | Pilot-ready | `PRODUCTION_SECRET_ROTATION.md` |
| Operations | log retention policy | Pilot-ready | `PRODUCTION_LOG_RETENTION.md` |
| Operations | monitoring/log shipping runbook | Pilot-ready | `PRODUCTION_MONITORING.md` |
| Production hardening | centralized log sink | Future | choose Wazuh/Indexer, Loki, or ELK |
| Production hardening | rate limiting | Future | not implemented |
| Production hardening | SSO | Future | not implemented |
| Production hardening | Redis/session split | Future | not implemented |
| Production hardening | worker/background jobs | Future | not implemented |
| Platform expansion | external notifications | Future | email/Slack/Telegram not implemented |
| Platform expansion | enrichment | Future | VirusTotal/Gemini/AI not implemented |
| Platform expansion | SOAR/destructive response | Future | intentionally excluded |

## Pilot-Ready Definition

A feature is pilot-ready when:

- it is implemented in the app or runbook
- it has smoke, regression, CI, or documented manual verification
- it does not require additional infrastructure beyond the current Docker Compose stack unless clearly marked as future work

## Production-Ready Definition

A feature becomes production-ready only after:

- centralized monitoring and log shipping are configured
- secret storage is externalized from local `.env`
- backup storage is off-host
- access, incident, and restore processes are approved by the owning team
- production-specific compliance requirements are satisfied
