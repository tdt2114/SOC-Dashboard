# Centralized Log Sink Decision

This decision record documents the recommended centralized log sink path for Repo B after the pilot.

## Context

Repo B currently has:

- Docker container logs
- backend `/health`
- runtime health report script
- smoke and regression tests
- GitHub Actions evidence
- PostgreSQL audit logs

This is enough for local validation and pilot handoff, but production needs centralized logs and alerts.

## Options Considered

| Option | Pros | Cons |
| --- | --- | --- |
| Wazuh/Indexer | aligns with SOC domain and existing Repo A stack | app logs and Wazuh security data need clear index separation |
| Loki/Grafana | lightweight app/container log dashboards | adds new stack outside current Wazuh setup |
| ELK/OpenSearch | powerful search and analytics | heavier operational footprint |
| Docker log retention only | simplest for pilot | not production-grade |

## Decision

Recommended pilot-to-production path:

1. Keep Docker log retention and `report_runtime_health.ps1` for the current pilot.
2. Use Wazuh/Indexer as the preferred production log sink if Repo A ownership agrees.
3. Use Loki/Grafana as the fallback if application operations need a separate lightweight dashboard.

Do not add ELK/OpenSearch in the next step unless there is an explicit enterprise requirement.

## Rationale

Wazuh/Indexer is the best first choice because the project is already SOC/Wazuh-centered. It keeps operational evidence close to the security platform and avoids adding another large stack before production need is proven.

Loki/Grafana is a reasonable fallback if the team wants app/service observability separated from security telemetry.

## Next Implementation Step

Before wiring log shipping:

- choose index naming or label strategy
- define which logs are shipped
- define retention in the sink
- define alert rules
- verify no secrets are emitted into logs
- add a test ingest event

Minimum logs to ship:

- `soc-backend`
- `soc-frontend`
- `soc-postgres`
- backup/restore script output
- CI failure summaries

## Decision Review

Review this decision after:

- pilot feedback
- first production-like deployment
- any incident where local logs were not enough
- any change to Repo A logging/indexing ownership
