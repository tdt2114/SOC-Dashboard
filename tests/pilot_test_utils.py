from __future__ import annotations

import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import Cookie
from typing import Any


ROLE_DEFAULTS = {
    "viewer": ("pilot_viewer", "PilotViewer123!ChangeMe"),
    "analyst": ("pilot_analyst", "PilotAnalyst123!ChangeMe"),
    "admin": ("pilot_admin", "PilotAdmin123!ChangeMe"),
}


@dataclass
class PilotResponse:
    status: int
    url: str
    body: str
    headers: dict[str, str]

    def json(self) -> Any:
        return json.loads(self.body) if self.body else None


def require_credentials() -> tuple[str, str]:
    username = (
        os.getenv("PILOT_TEST_USERNAME")
        or os.getenv("SMOKE_SUPERADMIN_USERNAME")
        or os.getenv("SEED_SUPERADMIN_USERNAME")
    )
    password = (
        os.getenv("PILOT_TEST_PASSWORD")
        or os.getenv("SMOKE_SUPERADMIN_PASSWORD")
        or os.getenv("SEED_SUPERADMIN_PASSWORD")
    )
    if not username or not password:
        raise RuntimeError(
            "Missing pilot test credentials. Set PILOT_TEST_USERNAME and PILOT_TEST_PASSWORD."
        )
    return username, password


def role_credentials(role: str) -> tuple[str, str]:
    normalized_role = role.strip().lower()
    if normalized_role not in ROLE_DEFAULTS:
        raise ValueError(f"Unknown pilot role {role!r}")

    default_username, default_password = ROLE_DEFAULTS[normalized_role]
    env_role = "ROLE_ADMIN" if normalized_role == "admin" else normalized_role.upper()
    pilot_role = normalized_role.upper()
    username = (
        os.getenv(f"PILOT_TEST_{pilot_role}_USERNAME")
        or os.getenv(f"SEED_{env_role}_USERNAME")
        or default_username
    )
    password = (
        os.getenv(f"PILOT_TEST_{pilot_role}_PASSWORD")
        or os.getenv(f"SEED_{env_role}_PASSWORD")
        or default_password
    )
    return username, password


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
    payload: dict[str, Any] | None = None,
    bearer_token: str | None = None,
) -> PilotResponse:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=20) as res:
            body = res.read().decode("utf-8", errors="replace")
            return PilotResponse(res.status, res.geturl(), body, dict(res.headers.items()))
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
            return PilotResponse(exc.code, exc.geturl(), body, dict(exc.headers.items()))
        finally:
            exc.close()


def path_of(url: str) -> str:
    return urllib.parse.urlparse(url).path


def query_of(url: str) -> str:
    return urllib.parse.urlparse(url).query


def header_value(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""
