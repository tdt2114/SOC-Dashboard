from __future__ import annotations

import os
import time
import unittest
import urllib.parse

from pilot_test_utils import make_opener, request, require_credentials, role_credentials


class PilotApiRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backend_url = os.getenv("PILOT_TEST_BACKEND_URL", "http://localhost:8000").rstrip("/")
        username, password = require_credentials()
        cls.opener, _ = make_opener()
        login = request(
            cls.opener,
            "POST",
            f"{cls.backend_url}/api/auth/login",
            payload={"username": username, "password": password},
        )
        if login.status != 200:
            raise RuntimeError(f"Backend login failed with HTTP {login.status}: {login.body}")
        payload = login.json()
        cls.access_token = payload["access_token"]
        cls.refresh_token = payload["refresh_token"]
        cls.current_user = payload["user"]

    def api(self, method: str, path: str, payload: dict | None = None, *, auth: bool = True):
        return request(
            self.opener,
            method,
            f"{self.backend_url}{path}",
            payload=payload,
            bearer_token=self.access_token if auth else None,
        )

    def login_as_role(self, role: str) -> tuple[str, dict]:
        username, password = role_credentials(role)
        opener, _ = make_opener()
        login = request(
            opener,
            "POST",
            f"{self.backend_url}/api/auth/login",
            payload={"username": username, "password": password},
        )
        self.assertEqual(login.status, 200, f"{role} login failed: {login.body}")
        payload = login.json()
        return payload["access_token"], payload["user"]

    def role_api(self, role: str, method: str, path: str, payload: dict | None = None):
        token, _user = self.login_as_role(role)
        opener, _ = make_opener()
        return request(opener, method, f"{self.backend_url}{path}", payload=payload, bearer_token=token)

    def first_alert(self) -> dict:
        alerts = self.api("GET", "/api/alerts?page=1&page_size=10").json()
        self.assertGreater(alerts["total"], 0, "pilot data should expose at least one alert")
        self.assertGreater(len(alerts["items"]), 0, "first alert page should not be empty")
        return alerts["items"][0]

    def test_health_auth_and_superadmin_routes(self) -> None:
        health = self.api("GET", "/health", auth=False)
        self.assertEqual(health.status, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(health.json()["database"], "ok")

        missing_token = self.api("GET", "/api/auth/me", auth=False)
        self.assertEqual(missing_token.status, 401)

        me = self.api("GET", "/api/auth/me")
        self.assertEqual(me.status, 200)
        self.assertEqual(me.json()["username"], self.current_user["username"])

        users_without_token = self.api("GET", "/api/users", auth=False)
        self.assertEqual(users_without_token.status, 401)

        users = self.api("GET", "/api/users")
        self.assertEqual(users.status, 200)
        self.assertIn("items", users.json())
        self.assertIn("roles", users.json())

    def test_alerts_agents_filters_pagination_and_detail(self) -> None:
        alerts = self.api("GET", "/api/alerts?page=1&page_size=10")
        self.assertEqual(alerts.status, 200)
        payload = alerts.json()
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 10)
        self.assertLessEqual(len(payload["items"]), 10)
        self.assertGreaterEqual(payload["total"], len(payload["items"]))

        three_month_alerts = self.api("GET", "/api/alerts?page=1&page_size=10&time_range=3m")
        self.assertEqual(three_month_alerts.status, 200)
        self.assertGreaterEqual(three_month_alerts.json()["total"], payload["total"])

        dashboard_three_months = self.api("GET", "/api/dashboard/summary?time_range=3m")
        self.assertEqual(dashboard_three_months.status, 200)
        self.assertGreaterEqual(dashboard_three_months.json()["total_alerts_24h"], payload["total"])

        high_alerts = self.api("GET", "/api/alerts?page=1&page_size=5&severity=high")
        self.assertEqual(high_alerts.status, 200)
        for item in high_alerts.json()["items"]:
            self.assertEqual(item["severity_label"], "high")

        first = payload["items"][0]
        detail = self.api("GET", f"/api/alerts/{first['id']}", auth=False)
        self.assertEqual(detail.status, 200)
        self.assertEqual(detail.json()["id"], first["id"])
        self.assertIn("raw", detail.json())

        agents = self.api("GET", "/api/agents", auth=False)
        self.assertEqual(agents.status, 200)
        agent_items = agents.json()["items"]
        self.assertGreater(len(agent_items), 0, "pilot data should expose at least one agent")

        named_agent = next((agent for agent in agent_items if agent.get("name")), None)
        if named_agent:
            filtered = self.api(
                "GET",
                f"/api/alerts?page=1&page_size=5&agent_name={named_agent['name']}",
                auth=False,
            )
            self.assertEqual(filtered.status, 200)
            for item in filtered.json()["items"]:
                self.assertEqual(item["agent"]["name"], named_agent["name"])

    def test_saved_search_crud_is_cleaned_up(self) -> None:
        name = f"pilot-api-regression-{int(time.time())}"
        created_id: int | None = None
        try:
            created = self.api(
                "POST",
                "/api/saved-searches",
                payload={
                    "name": name,
                    "filters": {"severity": "high", "time_range": "24h", "page_size": "10"},
                },
            )
            self.assertEqual(created.status, 201)
            created_payload = created.json()
            created_id = created_payload["id"]
            self.assertEqual(created_payload["name"], name)
            self.assertEqual(created_payload["filters"]["severity"], "high")

            listed = self.api("GET", "/api/saved-searches")
            self.assertEqual(listed.status, 200)
            self.assertTrue(any(item["id"] == created_id for item in listed.json()["items"]))

            renamed = f"{name}-renamed"
            updated = self.api(
                "PATCH",
                f"/api/saved-searches/{created_id}",
                payload={"name": renamed, "filters": {"rule_id": "550", "page_size": "15"}},
            )
            self.assertEqual(updated.status, 200)
            self.assertEqual(updated.json()["name"], renamed)
            self.assertEqual(updated.json()["filters"]["rule_id"], "550")
            self.assertNotIn("page_size", updated.json()["filters"])
        finally:
            if created_id is not None:
                deleted = self.api("DELETE", f"/api/saved-searches/{created_id}")
                self.assertEqual(deleted.status, 204)

        listed_after_delete = self.api("GET", "/api/saved-searches")
        self.assertEqual(listed_after_delete.status, 200)
        self.assertFalse(any(item["id"] == created_id for item in listed_after_delete.json()["items"]))

    def test_alert_workflow_bookmark_and_assignment_are_reversible(self) -> None:
        alert = self.first_alert()
        alert_id = alert["id"]

        workflow_without_token = self.api("GET", f"/api/alerts/{alert_id}/workflow", auth=False)
        self.assertEqual(workflow_without_token.status, 401)

        workflow = self.api("GET", f"/api/alerts/{alert_id}/workflow")
        self.assertEqual(workflow.status, 200)
        workflow_payload = workflow.json()
        self.assertIn("assignee_options", workflow_payload)

        bookmarked = self.api("POST", f"/api/alerts/{alert_id}/bookmark")
        self.assertEqual(bookmarked.status, 200)
        self.assertTrue(bookmarked.json()["is_bookmarked"])

        unbookmarked = self.api("DELETE", f"/api/alerts/{alert_id}/bookmark")
        self.assertEqual(unbookmarked.status, 200)
        self.assertFalse(unbookmarked.json()["is_bookmarked"])

        assignee_options = workflow_payload["assignee_options"]
        if assignee_options:
            assigned_user_id = assignee_options[0]["id"]
            assigned = self.api(
                "PATCH",
                f"/api/alerts/{alert_id}/workflow/assignment",
                payload={"assigned_user_id": assigned_user_id},
            )
            self.assertEqual(assigned.status, 200)
            self.assertEqual(assigned.json()["assignee"]["user_id"], assigned_user_id)

        unassigned = self.api(
            "PATCH",
            f"/api/alerts/{alert_id}/workflow/assignment",
            payload={"assigned_user_id": None},
        )
        self.assertEqual(unassigned.status, 200)
        self.assertIsNone(unassigned.json()["assignee"]["user_id"])

    def test_role_based_backend_permissions(self) -> None:
        viewer_token, viewer_user = self.login_as_role("viewer")
        self.assertEqual(viewer_user["roles"], ["viewer"])
        viewer_opener, _ = make_opener()
        viewer_saved_searches = request(
            viewer_opener,
            "GET",
            f"{self.backend_url}/api/saved-searches",
            bearer_token=viewer_token,
        )
        self.assertEqual(viewer_saved_searches.status, 403)
        viewer_cases = request(viewer_opener, "GET", f"{self.backend_url}/api/cases", bearer_token=viewer_token)
        self.assertEqual(viewer_cases.status, 403)
        viewer_users = request(viewer_opener, "GET", f"{self.backend_url}/api/users", bearer_token=viewer_token)
        self.assertEqual(viewer_users.status, 403)

        analyst_token, analyst_user = self.login_as_role("analyst")
        self.assertEqual(analyst_user["roles"], ["analyst"])
        analyst_opener, _ = make_opener()
        analyst_saved_searches = request(
            analyst_opener,
            "GET",
            f"{self.backend_url}/api/saved-searches",
            bearer_token=analyst_token,
        )
        self.assertEqual(analyst_saved_searches.status, 200)
        analyst_cases = request(analyst_opener, "GET", f"{self.backend_url}/api/cases", bearer_token=analyst_token)
        self.assertEqual(analyst_cases.status, 200)
        analyst_users = request(analyst_opener, "GET", f"{self.backend_url}/api/users", bearer_token=analyst_token)
        self.assertEqual(analyst_users.status, 403)

        admin_token, admin_user = self.login_as_role("admin")
        self.assertEqual(admin_user["roles"], ["admin"])
        self.assertFalse(admin_user["is_superuser"])
        admin_opener, _ = make_opener()
        admin_saved_searches = request(
            admin_opener,
            "GET",
            f"{self.backend_url}/api/saved-searches",
            bearer_token=admin_token,
        )
        self.assertEqual(admin_saved_searches.status, 200)
        admin_cases = request(admin_opener, "GET", f"{self.backend_url}/api/cases", bearer_token=admin_token)
        self.assertEqual(admin_cases.status, 200)
        admin_users = request(admin_opener, "GET", f"{self.backend_url}/api/users", bearer_token=admin_token)
        self.assertEqual(admin_users.status, 403)
        admin_audit = request(admin_opener, "GET", f"{self.backend_url}/api/audit-logs", bearer_token=admin_token)
        self.assertEqual(admin_audit.status, 403)

    def test_case_workflow_create_link_comment_update_and_close(self) -> None:
        alert = self.first_alert()
        alert_id = alert["id"]
        analyst_token, analyst_user = self.login_as_role("analyst")
        analyst_opener, _ = make_opener()
        title = f"pilot-api-case-regression-{int(time.time())}"
        case_id: int | None = None

        def case_request(method: str, path: str, payload: dict | None = None):
            return request(
                analyst_opener,
                method,
                f"{self.backend_url}{path}",
                payload=payload,
                bearer_token=analyst_token,
            )

        try:
            created = case_request(
                "POST",
                "/api/cases",
                payload={
                    "title": title,
                    "description": "Created by pilot API regression test.",
                    "status": "open",
                    "severity": "medium",
                    "alert_id": alert_id,
                },
            )
            self.assertEqual(created.status, 201)
            created_payload = created.json()
            case_id = created_payload["id"]
            self.assertEqual(created_payload["title"], title)
            self.assertEqual(created_payload["status"], "open")
            self.assertEqual(created_payload["severity"], "medium")
            self.assertEqual(created_payload["owner_user_id"], analyst_user["id"])
            self.assertTrue(any(item["alert_id"] == alert_id for item in created_payload["alerts"]))

            duplicate_link = case_request("POST", f"/api/cases/{case_id}/alerts", payload={"alert_id": alert_id})
            self.assertEqual(duplicate_link.status, 200)
            self.assertEqual(
                len([item for item in duplicate_link.json()["alerts"] if item["alert_id"] == alert_id]),
                1,
            )

            comment_text = f"pilot API case comment {int(time.time())}"
            commented = case_request("POST", f"/api/cases/{case_id}/comments", payload={"body": comment_text})
            self.assertEqual(commented.status, 200)
            self.assertTrue(any(item["body"] == comment_text for item in commented.json()["comments"]))

            updated = case_request(
                "PATCH",
                f"/api/cases/{case_id}",
                payload={
                    "status": "investigating",
                    "severity": "high",
                    "description": "Updated by pilot API regression test.",
                },
            )
            self.assertEqual(updated.status, 200)
            self.assertEqual(updated.json()["status"], "investigating")
            self.assertEqual(updated.json()["severity"], "high")

            detail = case_request("GET", f"/api/cases/{case_id}")
            self.assertEqual(detail.status, 200)
            self.assertEqual(detail.json()["id"], case_id)
            self.assertGreaterEqual(detail.json()["comment_count"], 1)
        finally:
            if case_id is not None:
                encoded_alert_id = urllib.parse.quote(alert_id, safe="")
                removed = case_request("DELETE", f"/api/cases/{case_id}/alerts/{encoded_alert_id}")
                self.assertEqual(removed.status, 200)
                self.assertFalse(any(item["alert_id"] == alert_id for item in removed.json()["alerts"]))

                closed = case_request(
                    "PATCH",
                    f"/api/cases/{case_id}",
                    payload={
                        "title": f"{title} [closed by regression]",
                        "status": "closed",
                        "severity": "low",
                    },
                )
                self.assertEqual(closed.status, 200)
                self.assertEqual(closed.json()["status"], "closed")
                self.assertEqual(closed.json()["severity"], "low")

    def test_soar_action_request_approve_and_reject(self) -> None:
        soar_token = os.getenv("SOAR_WEBHOOK_TOKEN") or os.getenv("PILOT_TEST_SOAR_TOKEN")
        if not soar_token:
            self.skipTest("SOAR_WEBHOOK_TOKEN not set; SOAR intake endpoint disabled")

        backend = self.backend_url
        soar_opener, _ = make_opener()

        def soar_create(payload: dict):
            return request(
                soar_opener,
                "POST",
                f"{backend}/api/actions",
                payload=payload,
                extra_headers={"X-SOAR-Token": soar_token},
            )

        invalid_token = request(
            soar_opener,
            "POST",
            f"{backend}/api/actions",
            payload={"action_type": "isolate-host", "target_agent_id": "001"},
            extra_headers={"X-SOAR-Token": "wrong-token"},
        )
        self.assertEqual(invalid_token.status, 401)

        unsupported = soar_create({"action_type": "format-disk", "target_agent_id": "001"})
        self.assertEqual(unsupported.status, 400)

        created = soar_create(
            {
                "action_type": "isolate-host",
                "target_agent_id": "001",
                "reason": "pilot regression isolate",
                "rule_id": "100010",
            }
        )
        self.assertEqual(created.status, 201, created.body)
        created_payload = created.json()
        token = created_payload["token"]
        self.assertEqual(created_payload["status"], "pending")
        self.assertEqual(created_payload["command"], "isolate-host")
        self.assertTrue(created_payload["approval_path"].endswith("/approve"))

        viewer_token, _ = self.login_as_role("viewer")
        viewer_opener, _ = make_opener()
        viewer_list = request(viewer_opener, "GET", f"{backend}/api/actions", bearer_token=viewer_token)
        self.assertEqual(viewer_list.status, 403)

        analyst_token, _ = self.login_as_role("analyst")
        analyst_opener, _ = make_opener()
        analyst_list = request(
            analyst_opener,
            "GET",
            f"{backend}/api/actions?status=pending",
            bearer_token=analyst_token,
        )
        self.assertEqual(analyst_list.status, 200)
        self.assertTrue(any(item["token"] == token for item in analyst_list.json()["items"]))

        analyst_approve = request(
            analyst_opener,
            "POST",
            f"{backend}/api/actions/{token}/approve",
            bearer_token=analyst_token,
        )
        self.assertEqual(analyst_approve.status, 403)

        admin_token, _ = self.login_as_role("admin")
        admin_opener, _ = make_opener()
        approved = request(
            admin_opener,
            "POST",
            f"{backend}/api/actions/{token}/approve",
            bearer_token=admin_token,
        )
        self.assertEqual(approved.status, 200, approved.body)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertIn(approved.json()["execution_status"], ["success", "failed", "skipped"])

        reapprove = request(
            admin_opener,
            "POST",
            f"{backend}/api/actions/{token}/approve",
            bearer_token=admin_token,
        )
        self.assertEqual(reapprove.status, 409)

        second = soar_create(
            {"action_type": "kill-process", "target_agent_id": "001", "reason": "pilot regression kill"}
        )
        self.assertEqual(second.status, 201)
        second_token = second.json()["token"]
        rejected = request(
            admin_opener,
            "POST",
            f"{backend}/api/actions/{second_token}/reject",
            payload={"reason": "false positive"},
            bearer_token=admin_token,
        )
        self.assertEqual(rejected.status, 200)
        self.assertEqual(rejected.json()["status"], "rejected")

    def test_ai_alert_analysis(self) -> None:
        alert = self.first_alert()
        alert_id = alert["id"]
        backend = self.backend_url

        # viewer must not be able to run AI analysis
        viewer_token, _ = self.login_as_role("viewer")
        viewer_opener, _ = make_opener()
        viewer_run = request(
            viewer_opener,
            "POST",
            f"{backend}/api/alerts/{urllib.parse.quote(alert_id, safe='')}/ai-analyze",
            bearer_token=viewer_token,
        )
        self.assertEqual(viewer_run.status, 403)

        analyst_token, _ = self.login_as_role("analyst")
        analyst_opener, _ = make_opener()
        quoted = urllib.parse.quote(alert_id, safe="")

        run = request(
            analyst_opener,
            "POST",
            f"{backend}/api/alerts/{quoted}/ai-analyze",
            bearer_token=analyst_token,
        )
        if run.status == 503:
            self.skipTest("AI disabled (AI_ENABLED not set)")
        self.assertEqual(run.status, 200, run.body)
        body = run.json()
        self.assertEqual(body["entity_type"], "alert")
        self.assertEqual(body["entity_ref"], alert_id)
        self.assertTrue(body["summary"])
        self.assertIn(
            body["recommended_action"],
            ["block_ip", "isolate_host", "kill_process", "monitor", "none", None],
        )

        # cached read should now return the same analysis
        cached = request(
            analyst_opener,
            "GET",
            f"{backend}/api/alerts/{quoted}/ai-analysis",
            bearer_token=analyst_token,
        )
        self.assertEqual(cached.status, 200)
        self.assertEqual(cached.json()["id"], body["id"])

    def test_ai_pending_action_and_case_summary(self) -> None:
        soar_token = os.getenv("SOAR_WEBHOOK_TOKEN") or os.getenv("PILOT_TEST_SOAR_TOKEN")
        if not soar_token:
            self.skipTest("SOAR_WEBHOOK_TOKEN not set")

        backend = self.backend_url
        analyst_token, analyst_user = self.login_as_role("analyst")
        analyst_opener, _ = make_opener()

        # AI on a pending action (SOAR approval assist)
        soar_opener, _ = make_opener()
        created = request(
            soar_opener,
            "POST",
            f"{backend}/api/actions",
            payload={"action_type": "isolate-host", "target_agent_id": "001", "reason": "ai-2 regression"},
            extra_headers={"X-SOAR-Token": soar_token},
        )
        self.assertEqual(created.status, 201)
        token = created.json()["token"]

        ai_action = request(
            analyst_opener,
            "POST",
            f"{backend}/api/actions/{token}/ai-analyze",
            bearer_token=analyst_token,
        )
        if ai_action.status == 503:
            self.skipTest("AI disabled")
        self.assertEqual(ai_action.status, 200, ai_action.body)
        self.assertEqual(ai_action.json()["entity_type"], "pending_action")

        # AI summary on a case
        case = request(
            analyst_opener,
            "POST",
            f"{backend}/api/cases",
            payload={"title": f"ai-2 case {int(time.time())}", "status": "open", "severity": "medium"},
            bearer_token=analyst_token,
        )
        self.assertEqual(case.status, 201)
        case_id = case.json()["id"]
        try:
            ai_case = request(
                analyst_opener,
                "POST",
                f"{backend}/api/cases/{case_id}/ai-summary",
                bearer_token=analyst_token,
            )
            self.assertEqual(ai_case.status, 200, ai_case.body)
            self.assertEqual(ai_case.json()["entity_type"], "case")
            self.assertEqual(ai_case.json()["entity_ref"], str(case_id))
        finally:
            request(
                analyst_opener,
                "PATCH",
                f"{backend}/api/cases/{case_id}",
                payload={"status": "closed"},
                bearer_token=analyst_token,
            )


if __name__ == "__main__":
    unittest.main()
