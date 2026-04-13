# soc-dashboard

Repo B MVP scaffold for consuming data from Repo A.

## Scope locked by plan

This scaffold follows:

- `Plan/RepoA-to-RepoB-Contract.md`
- `Plan/RepoB-MVP-Spec.md`

The current repo only covers the MVP baseline:

- Alert list
- Alert detail
- Agent list
- PostgreSQL foundation
- Alembic scaffold

It does not include:

- AI features
- SOAR workflows
- Telegram or Slack delivery
- VirusTotal enrichment
- destructive active response
- mobile support

## Structure

```text
soc-dashboard/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── Dockerfile
├── .env.example
└── docker-compose.yml
```

## Backend contract

### Internal endpoints

- `GET /health`
- `GET /api/alerts`
- `GET /api/alerts/{id}`
- `GET /api/agents`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Data sources

- Wazuh Indexer for alert list, detail, search, filter
- Wazuh API for agent list and agent status

### Normalized alert fields

- `timestamp`
- `agent.name`
- `agent.id`
- `rule.id`
- `rule.level`
- `rule.description`
- `data.srcip`
- `syscheck.path`

Missing fields are handled as optional and rendered as `N/A`.

### App database foundation

Repo B now includes:

- PostgreSQL in `docker-compose.yml`
- async SQLAlchemy engine and session
- Alembic scaffold for future migrations

## Frontend pages

- `/alerts`
- `/alerts/[id]`
- `/agents`

## Local startup

1. Copy `.env.example` to `.env`
2. For standalone Repo B testing, keep `MOCK_MODE=true`
3. For live integration, set `MOCK_MODE=false` and adjust the Wazuh URLs and credentials if needed
4. Run `docker compose up --build`
5. Open `http://localhost:3000`

## Database startup

By default the stack now starts:

- `soc-postgres`
- `soc-backend`
- `soc-frontend`

The backend health endpoint now reports:

- app mode: `mock` or `live`
- database status: `ok` or `unavailable`

## Alembic

Migration scaffold lives in:

- `backend/alembic.ini`
- `backend/alembic/`

Typical commands:

```bash
cd backend
alembic revision -m "create users table"
alembic upgrade head
```

Initial schema already scaffolded in this repo:

- `departments`
- `roles`
- `users`
- `user_roles`
- `refresh_tokens` after the second migration

To apply it inside the running backend container:

```bash
docker exec -it soc-backend sh
alembic upgrade head
```

To verify from PostgreSQL:

```bash
docker exec -it soc-postgres psql -U soc_dashboard -d soc_dashboard
\dt
```

## Seeded accounts

Initial seed script creates:

- 1 default department
- roles: `admin`, `analyst`, `viewer`
- 1 `admin` account
- 1 `superadmin` account

Seed command:

```bash
docker exec -it soc-backend sh -lc "python -m app.scripts.seed_initial_data"
```

Credentials come from `.env`:

- `SEED_ADMIN_USERNAME`
- `SEED_ADMIN_PASSWORD`
- `SEED_SUPERADMIN_USERNAME`
- `SEED_SUPERADMIN_PASSWORD`

Change these defaults immediately outside local dev.

## Test modes

### Mode A: Standalone Repo B test

Use:

- `MOCK_MODE=true`

What you can verify:

- backend boots
- frontend boots
- `/health` returns `mode: mock`
- `/alerts` renders fixture alerts
- `/agents` renders fixture agents

### Mode B: Live integration test

Use:

- `MOCK_MODE=false`

What you need:

- Repo A running and reachable on `:55000` and `:9200`

What you can verify:

- live alerts from Indexer
- live agents from Wazuh API
- real contract checks for `100001`, `100064`, and `550`

## Connection modes

### Mode 1: Repo A and Repo B run separately

Use the defaults in `.env.example`:

- `WAZUH_API_BASE_URL=https://host.docker.internal:55000`
- `WAZUH_INDEXER_URL=https://host.docker.internal:9200`

This is the least disruptive mode because Repo A does not need compose changes.

### Mode 2: Repo A and Repo B share one compose network

Switch the env values to:

- `WAZUH_API_BASE_URL=https://wazuh-manager:55000`
- `WAZUH_INDEXER_URL=https://wazuh-indexer:9200`

Use this mode only when you intentionally merge the runtime network.

## Next implementation step

This scaffold is ready for the next phase:

- connect to live Repo A data
- verify alerts `100001`, `100064`, and `550`
- add auth and users modules on top of PostgreSQL foundation
