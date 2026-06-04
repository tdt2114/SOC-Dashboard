from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import Cookie


@dataclass
class Response:
    status: int
    url: str
    body: str
    headers: dict[str, str]


def make_cookie(name: str, value: str, domain: str) -> Cookie:
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=False,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


def make_opener() -> tuple[urllib.request.OpenerDirector, http.cookiejar.CookieJar]:
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    return opener, cookie_jar


def request(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    *,
    payload: dict[str, object] | None = None,
) -> Response:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=15) as res:
            body = res.read().decode("utf-8", errors="replace")
            return Response(res.status, res.geturl(), body, dict(res.headers.items()))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return Response(exc.code, exc.geturl(), body, dict(exc.headers.items()))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_status(response: Response, expected: int, label: str) -> None:
    assert_true(
        response.status == expected,
        f"{label}: expected HTTP {expected}, got {response.status} at {response.url}",
    )


def path_of(url: str) -> str:
    return urllib.parse.urlparse(url).path


def header_value(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def run(args: argparse.Namespace) -> list[str]:
    frontend = args.frontend_url.rstrip("/")
    backend = args.backend_url.rstrip("/")
    username = args.username or os.getenv("SMOKE_SUPERADMIN_USERNAME") or os.getenv("SEED_SUPERADMIN_USERNAME")
    password = args.password or os.getenv("SMOKE_SUPERADMIN_PASSWORD") or os.getenv("SEED_SUPERADMIN_PASSWORD")

    if not username or not password:
        raise AssertionError(
            "Missing credentials. Set SMOKE_SUPERADMIN_USERNAME and SMOKE_SUPERADMIN_PASSWORD, "
            "or pass --username and --password."
        )

    checks: list[str] = []

    public_opener, _ = make_opener()
    health = request(public_opener, "GET", f"{backend}/health")
    assert_status(health, 200, "backend health")
    health_payload = json.loads(health.body)
    assert_true(health_payload.get("status") == "ok", "backend health status is not ok")
    assert_true(health_payload.get("database") == "ok", "backend database status is not ok")
    checks.append(f"backend health ok ({health_payload.get('mode')})")

    login_page = request(public_opener, "GET", f"{frontend}/login")
    assert_status(login_page, 200, "login page")
    assert_true("Sign In" in login_page.body, "login page did not render Sign In")
    checks.append("login page renders")

    stale_opener, stale_cookies = make_opener()
    host = urllib.parse.urlparse(frontend).hostname or "localhost"
    stale_cookies.set_cookie(make_cookie("soc_access_token", "bad-token", host))
    stale_alerts = request(stale_opener, "GET", f"{frontend}/alerts")
    assert_status(stale_alerts, 200, "stale-cookie alerts")
    assert_true(path_of(stale_alerts.url) == "/login", "stale cookie did not redirect to login")
    assert_true("next=%2Falerts" in urllib.parse.urlparse(stale_alerts.url).query, "stale cookie lost next=/alerts")
    assert_true("Sign In" in stale_alerts.body, "stale cookie login page did not render")
    checks.append("stale cookie redirects to login")

    auth_opener, _ = make_opener()
    login = request(
        auth_opener,
        "POST",
        f"{frontend}/api/auth/login",
        payload={"username": username, "password": password},
    )
    assert_status(login, 200, "frontend login")
    assert_true("user" in login.body, "login response did not include user")
    checks.append("frontend login succeeds")

    protected_routes = {
        "/dashboard": "Dashboard",
        "/alerts": "Alert List",
        "/cases": "Cases",
        "/users": "Users",
        "/audit-logs": "Audit Logs",
        "/settings": "System Settings",
    }
    for route, marker in protected_routes.items():
        response = request(auth_opener, "GET", f"{frontend}{route}")
        assert_status(response, 200, route)
        assert_true(path_of(response.url) == route, f"{route}: unexpectedly landed at {response.url}")
        assert_true(marker in response.body, f"{route}: missing marker {marker!r}")
        if route == "/alerts":
            assert_true("Showing" in response.body, "alerts page missing pagination summary")
            assert_true("Next" in response.body, "alerts page missing Next pagination action")
        checks.append(f"{route} renders")

        if route == "/alerts":
            match = re.search(r'href="/alerts/([^"]+)"', response.body)
            if match:
                detail_path = f"/alerts/{match.group(1)}"
                detail = request(auth_opener, "GET", f"{frontend}{detail_path}")
                assert_status(detail, 200, detail_path)
                assert_true("Alert Triage" in detail.body, "alert detail missing Alert Triage eyebrow")
                assert_true("Back to alerts" in detail.body, "alert detail missing Back to alerts action")
                assert_true("Raw JSON" in detail.body, "alert detail missing Raw JSON section")
                checks.append("alert detail renders with back action")

    export_routes = [
        "/api/exports/alerts.csv",
        "/api/exports/cases.csv",
        "/api/exports/audit-logs.csv",
    ]
    for route in export_routes:
        response = request(auth_opener, "GET", f"{frontend}{route}")
        assert_status(response, 200, route)
        content_type = header_value(response.headers, "Content-Type")
        assert_true("text/csv" in content_type, f"{route}: expected text/csv, got {content_type!r}")
        assert_true("," in response.body, f"{route}: response does not look like CSV")
        checks.append(f"{route} exports CSV")

    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Repo B pilot smoke checks.")
    parser.add_argument("--frontend-url", default=os.getenv("SMOKE_FRONTEND_URL", "http://localhost:3000"))
    parser.add_argument("--backend-url", default=os.getenv("SMOKE_BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    return parser.parse_args()


def main() -> int:
    try:
        checks = run(parse_args())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    for check in checks:
        print(f"PASS: {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
