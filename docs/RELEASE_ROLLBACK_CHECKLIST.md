# Release and Rollback Checklist

This checklist defines how to release Repo B changes and how to roll back if verification fails.

## Release Scope

Every release should identify:

- commit or tag
- changed modules or docs
- database migration impact
- configuration changes
- operational runbook changes
- test evidence

## Release Checklist

Before release:

- GitHub Actions `Pilot Regression` passes
- local smoke passes
- local regression passes when runtime-affecting code changed
- backup exists before migration or bulk data operation
- restore drill passes before production-like deployment
- `.env` mode is correct
- seeded superadmin credential is available to the operator
- known gaps are documented

Commands:

```powershell
git status -sb
.\scripts\report_runtime_health.ps1
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

## Rollback Trigger

Rollback if any of these occur after release:

- backend `/health` fails
- database health is not `ok`
- frontend `/login` fails
- login is broken for superadmin
- alert or case route returns blank page or server error
- migrations fail
- smoke test fails
- regression suite fails on core auth, alert, or case workflow

## Rollback Procedure

1. Stop user access if the environment is production-like.
2. Preserve logs and command output.
3. Revert to the previous known-good commit or deployment artifact.
4. Restore database from the pre-release backup if schema/data changed.
5. Run migrations.
6. Run runtime health report.
7. Run smoke and regression tests.
8. Record rollback result.

Commands:

```powershell
docker compose up -d --build
docker compose exec -T soc-backend alembic upgrade head
.\scripts\report_runtime_health.ps1
python scripts\smoke_pilot.py --username "<superadmin-username>" --password "<superadmin-password>"
python -m unittest discover -s tests -v
```

If database restore is needed, follow [PRODUCTION_RESTORE_APPROVAL.md](PRODUCTION_RESTORE_APPROVAL.md).

## Rollback Record Template

```text
Rollback:
Environment:
Failed release commit:
Rollback target:
Reason:
Backup restored:
Operator:
Approver:
Runtime health:
Smoke:
Regression:
User impact:
Notes:
```
