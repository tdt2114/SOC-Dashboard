param(
    [int]$RegressionRetentionDays = 30,
    [int]$PilotRetentionDays = 90
)

$ErrorActionPreference = "Stop"

$database = (docker compose exec -T soc-postgres printenv POSTGRES_DB).Trim()
$username = (docker compose exec -T soc-postgres printenv POSTGRES_USER).Trim()

if (-not $database -or -not $username) {
    throw "Unable to read POSTGRES_DB or POSTGRES_USER from soc-postgres."
}

Write-Output "Case retention report"
Write-Output "Database: $database"
Write-Output "Regression retention days: $RegressionRetentionDays"
Write-Output "Pilot retention days: $PilotRetentionDays"
Write-Output ""

Write-Output "Cases by status:"
docker compose exec -T soc-postgres psql -U $username -d $database -P pager=off -c @"
select status, count(*) as total
from cases
group by status
order by status;
"@

Write-Output ""
Write-Output "Closed regression cases past retention:"
docker compose exec -T soc-postgres psql -U $username -d $database -P pager=off -c @"
select id, title, status, updated_at::date as closed_or_updated_date
from cases
where status = 'closed'
  and (
    title like 'pilot-api-case-regression-%'
    or title like 'pilot-ui-case-regression-%'
  )
  and updated_at < now() - interval '$RegressionRetentionDays days'
order by updated_at asc, id asc;
"@

Write-Output ""
Write-Output "Closed pilot cases past retention:"
docker compose exec -T soc-postgres psql -U $username -d $database -P pager=off -c @"
select id, title, status, updated_at::date as closed_or_updated_date
from cases
where status = 'closed'
  and title not like 'pilot-api-case-regression-%'
  and title not like 'pilot-ui-case-regression-%'
  and updated_at < now() - interval '$PilotRetentionDays days'
order by updated_at asc, id asc;
"@

Write-Output ""
Write-Output "Report only. No data was changed."
