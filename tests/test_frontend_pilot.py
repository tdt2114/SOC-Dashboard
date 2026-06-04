from __future__ import annotations

import os
import re
import time
import urllib.parse
import unittest

from pilot_test_utils import make_cookie, make_opener, path_of, query_of, request, require_credentials, role_credentials


class PilotFrontendRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frontend_url = os.getenv("PILOT_TEST_FRONTEND_URL", "http://localhost:3000").rstrip("/")
        username, password = require_credentials()
        cls.opener, _ = make_opener()
        login = request(
            cls.opener,
            "POST",
            f"{cls.frontend_url}/api/auth/login",
            payload={"username": username, "password": password},
        )
        if login.status != 200:
            raise RuntimeError(f"Frontend login failed with HTTP {login.status}: {login.body}")

    def page(self, path: str):
        return request(self.opener, "GET", f"{self.frontend_url}{path}")

    def login_frontend_as_role(self, role: str):
        username, password = role_credentials(role)
        opener, _ = make_opener()
        login = request(
            opener,
            "POST",
            f"{self.frontend_url}/api/auth/login",
            payload={"username": username, "password": password},
        )
        self.assertEqual(login.status, 200, f"{role} frontend login failed: {login.body}")
        return opener

    def test_stale_cookie_redirects_to_login_without_loop(self) -> None:
        stale_opener, stale_cookies = make_opener()
        host = urllib.parse.urlparse(self.frontend_url).hostname or "localhost"
        stale_cookies.set_cookie(make_cookie("soc_access_token", "bad-token", host))

        response = request(stale_opener, "GET", f"{self.frontend_url}/alerts")
        self.assertEqual(response.status, 200)
        self.assertEqual(path_of(response.url), "/login")
        self.assertIn("next=%2Falerts", query_of(response.url))
        self.assertIn("Sign In", response.body)

    def test_protected_routes_render_expected_markers(self) -> None:
        routes = {
            "/dashboard": "Dashboard",
            "/alerts": "Alert List",
            "/agents": "Agents",
            "/cases": "Cases",
            "/users": "Users",
            "/audit-logs": "Audit Logs",
            "/settings": "System Settings",
        }
        for route, marker in routes.items():
            with self.subTest(route=route):
                response = self.page(route)
                self.assertEqual(response.status, 200)
                self.assertEqual(path_of(response.url), route)
                self.assertIn(marker, response.body)

    def test_alerts_page_has_compact_filters_agent_dropdown_and_pagination(self) -> None:
        response = self.page("/alerts?page_size=10")
        self.assertEqual(response.status, 200)
        body = response.body

        self.assertIn("Agent Name", body)
        self.assertIn("All agents", body)
        self.assertIn("Wazuh Manager", body)
        self.assertIn("SOC-Server-Dev", body)
        self.assertIn("Saved search", body)
        self.assertIn("Save current", body)
        self.assertNotIn("Saved Searches", body)
        self.assertNotIn("Save current filters", body)
        self.assertNotIn("Name this filter set", body)
        self.assertIn("10 per page", body)
        self.assertIn("15 per page", body)
        self.assertIn("Showing", body)
        self.assertIn("Next", body)

        page_two = self.page("/alerts?page=2&page_size=10")
        self.assertEqual(page_two.status, 200)
        self.assertIn("Showing", page_two.body)
        self.assertIn("Previous", page_two.body)

    def test_alert_detail_keeps_back_action_and_raw_json(self) -> None:
        alerts = self.page("/alerts?page_size=10")
        self.assertEqual(alerts.status, 200)
        match = re.search(r'href="/alerts/([^"]+)"', alerts.body)
        self.assertIsNotNone(match, "alerts page should link to at least one alert detail")

        detail = self.page(f"/alerts/{match.group(1)}")
        self.assertEqual(detail.status, 200)
        self.assertIn("Alert Triage", detail.body)
        self.assertIn("Back to alerts", detail.body)
        self.assertIn("Related Agent", detail.body)
        self.assertIn("Raw JSON", detail.body)

    def test_frontend_saved_search_proxy_create_apply_delete_flow(self) -> None:
        name = f"pilot-ui-regression-{int(time.time())}"
        created_id: int | None = None
        try:
            created = request(
                self.opener,
                "POST",
                f"{self.frontend_url}/api/saved-searches",
                payload={
                    "name": name,
                    "filters": {"severity": "high", "time_range": "24h", "page_size": "10"},
                },
            )
            self.assertEqual(created.status, 201)

            listed = request(self.opener, "GET", f"{self.frontend_url}/api/saved-searches")
            self.assertEqual(listed.status, 200)
            match = next((item for item in listed.json()["items"] if item["name"] == name), None)
            self.assertIsNotNone(match)
            created_id = match["id"]

            filtered_page = self.page("/alerts?severity=high&time_range=24h&page_size=10")
            self.assertEqual(filtered_page.status, 200)
            self.assertIn("severity-high", filtered_page.body)
        finally:
            if created_id is not None:
                deleted = request(
                    self.opener,
                    "DELETE",
                    f"{self.frontend_url}/api/saved-searches/{created_id}",
                )
                self.assertEqual(deleted.status, 204)

    def test_role_based_frontend_navigation_and_access_states(self) -> None:
        viewer = self.login_frontend_as_role("viewer")
        viewer_dashboard = request(viewer, "GET", f"{self.frontend_url}/dashboard")
        self.assertEqual(viewer_dashboard.status, 200)
        self.assertIn("Operations", viewer_dashboard.body)
        self.assertNotIn("Workflow", viewer_dashboard.body)
        self.assertNotIn("Administration", viewer_dashboard.body)

        viewer_cases = request(viewer, "GET", f"{self.frontend_url}/cases")
        self.assertEqual(viewer_cases.status, 200)
        self.assertIn("Analyst or admin access required", viewer_cases.body)

        analyst = self.login_frontend_as_role("analyst")
        analyst_dashboard = request(analyst, "GET", f"{self.frontend_url}/dashboard")
        self.assertEqual(analyst_dashboard.status, 200)
        self.assertIn("Workflow", analyst_dashboard.body)
        self.assertNotIn("Administration", analyst_dashboard.body)

        analyst_cases = request(analyst, "GET", f"{self.frontend_url}/cases")
        self.assertEqual(analyst_cases.status, 200)
        self.assertIn("Case", analyst_cases.body)
        self.assertNotIn("Analyst or admin access required", analyst_cases.body)

        admin = self.login_frontend_as_role("admin")
        admin_dashboard = request(admin, "GET", f"{self.frontend_url}/dashboard")
        self.assertEqual(admin_dashboard.status, 200)
        self.assertIn("Workflow", admin_dashboard.body)
        self.assertNotIn("Administration", admin_dashboard.body)

        admin_users = request(admin, "GET", f"{self.frontend_url}/users")
        self.assertEqual(admin_users.status, 200)
        self.assertIn("Superadmin access required", admin_users.body)

    def test_frontend_case_proxy_workflow_create_comment_update_and_close(self) -> None:
        analyst = self.login_frontend_as_role("analyst")
        alerts_page = request(analyst, "GET", f"{self.frontend_url}/alerts?page_size=10")
        self.assertEqual(alerts_page.status, 200)
        match = re.search(r'href="/alerts/([^"]+)"', alerts_page.body)
        self.assertIsNotNone(match, "alerts page should link to at least one alert detail")
        alert_id = urllib.parse.unquote(match.group(1))
        title = f"pilot-ui-case-regression-{int(time.time())}"
        case_id: int | None = None

        try:
            created = request(
                analyst,
                "POST",
                f"{self.frontend_url}/api/cases",
                payload={
                    "title": title,
                    "description": "Created by pilot frontend proxy regression test.",
                    "status": "open",
                    "severity": "medium",
                    "alert_id": alert_id,
                },
            )
            self.assertEqual(created.status, 201)
            created_payload = created.json()
            case_id = created_payload["id"]
            self.assertEqual(created_payload["title"], title)
            self.assertTrue(any(item["alert_id"] == alert_id for item in created_payload["alerts"]))

            comment_text = f"pilot frontend case comment {int(time.time())}"
            commented = request(
                analyst,
                "POST",
                f"{self.frontend_url}/api/cases/{case_id}/comments",
                payload={"body": comment_text},
            )
            self.assertEqual(commented.status, 200)
            self.assertTrue(any(item["body"] == comment_text for item in commented.json()["comments"]))

            updated = request(
                analyst,
                "PATCH",
                f"{self.frontend_url}/api/cases/{case_id}",
                payload={"status": "investigating", "severity": "high"},
            )
            self.assertEqual(updated.status, 200)
            self.assertEqual(updated.json()["status"], "investigating")
            self.assertEqual(updated.json()["severity"], "high")

            case_page = request(analyst, "GET", f"{self.frontend_url}/cases/{case_id}")
            self.assertEqual(case_page.status, 200)
            self.assertIn(title, case_page.body)
            self.assertIn(comment_text, case_page.body)
        finally:
            if case_id is not None:
                encoded_alert_id = urllib.parse.quote(alert_id, safe="")
                removed = request(
                    analyst,
                    "DELETE",
                    f"{self.frontend_url}/api/cases/{case_id}/alerts/{encoded_alert_id}",
                )
                self.assertEqual(removed.status, 200)

                closed = request(
                    analyst,
                    "PATCH",
                    f"{self.frontend_url}/api/cases/{case_id}",
                    payload={
                        "title": f"{title} [closed by regression]",
                        "status": "closed",
                        "severity": "low",
                    },
                )
                self.assertEqual(closed.status, 200)
                self.assertEqual(closed.json()["status"], "closed")


if __name__ == "__main__":
    unittest.main()
