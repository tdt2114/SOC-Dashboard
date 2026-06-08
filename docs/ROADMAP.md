# Repo B Roadmap

This roadmap keeps Repo B aligned with the original product plan: Repo A remains the security core, while Repo B owns product UX, users, workflow, cases, audit, and operations.

## Current Phase: Pilot-Ready Product

Completed:

- stable mock and live modes
- PostgreSQL application database
- internal auth and role-based access
- user management
- audit logs
- alert list/detail and agent inventory
- saved searches, bookmarks, assignments, notes, and notifications
- case workflow
- exports
- dashboard summary
- CI, smoke, and regression tests
- backup, restore drill, retention, monitoring, secret rotation, and handoff runbooks

Goal:

- use Repo B in a controlled internal SOC pilot
- collect operator feedback
- validate alert triage and case workflow
- verify live Repo A integration before handoff

## Next Phase: Production Hardening

Recommended order:

1. Choose and configure centralized production log sink.
2. Add production monitoring dashboards and alerts.
3. Move secrets out of local `.env` into an approved secret store.
4. Add rate limiting and stronger session controls.
5. Define backup off-host storage and lifecycle policy.
6. Add production incident response checklist.
7. Add production deployment and rollback checklist.

Candidate log sink choices:

- Wazuh/Indexer for SOC-domain alignment
- Loki/Grafana for lightweight app operations dashboards
- ELK/OpenSearch for heavier enterprise analytics

## Future Platform Expansion

Add only after pilot feedback confirms the need:

- SSO
- Redis/session store split
- worker/background jobs
- external notification delivery
- enrichment integrations
- report generation
- case archive automation
- SOAR or active response
- AI-assisted triage

## Explicit Non-Goals For Current Pilot

- destructive response workflows
- AI decision-making
- replacing Repo A detection
- replacing Wazuh Indexer alert retention
- mobile-specific UI
- multi-tenant enterprise deployment

## Exit Criteria For Pilot

The pilot can be considered successful when:

- operators can complete alert triage from `/alerts` to `/cases`
- role boundaries are accepted by the team
- live alerts and agents load reliably from Repo A
- audit logs capture relevant user/admin actions
- CSV exports support handoff or investigation notes
- CI remains green after pilot feedback changes
- backup and restore drill remain usable
- monitoring report catches basic service failures

## Decision Point After Pilot

After the pilot, choose one path:

- harden for production deployment
- keep as internal SOC tool
- expand into SOC platform with notifications, enrichment, and automation

Do not start SOAR, AI, or broad integrations until the pilot validates the core workflow.
