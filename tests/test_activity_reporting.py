import json
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import httpx


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "coffee_api"))


class ActivityReportingTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def module():
        from src import main
        return main

    async def test_report_activity_sends_only_product_and_subject(self):
        main = self.module()
        seen = {}

        async def handler(request):
            seen["request"] = request
            return httpx.Response(200)

        transport = httpx.MockTransport(handler)
        original = httpx.AsyncClient
        with (
            patch.object(main, "ANALYTICS_URL", "http://analytics:8080"),
            patch.object(main, "ANALYTICS_TOKEN", "secret"),
            patch.object(
                main.httpx,
                "AsyncClient",
                side_effect=lambda **kwargs: original(transport=transport, **kwargs),
            ),
        ):
            await main.report_activity("did:privy:user", "person@example.com", "Person", "app_open")

        request = seen["request"]
        self.assertEqual(request.headers["authorization"], "Bearer secret")
        self.assertEqual(str(request.url), "http://analytics:8080/v1/activity")
        self.assertEqual(
            json.loads(request.content),
            {
                "product": "ezcoffee",
                "subject": "did:privy:user",
                "event": "app_open",
                "email": "person@example.com",
                "name": "Person",
            },
        )

    async def test_report_activity_is_best_effort(self):
        main = self.module()
        async def handler(_):
            raise httpx.ConnectError("offline")

        transport = httpx.MockTransport(handler)
        original = httpx.AsyncClient
        with (
            patch.object(main, "ANALYTICS_URL", "http://analytics:8080"),
            patch.object(main, "ANALYTICS_TOKEN", "secret"),
            patch.object(
                main.httpx,
                "AsyncClient",
                side_effect=lambda **kwargs: original(transport=transport, **kwargs),
            ),
        ):
            await main.report_activity("did:privy:user")

    async def test_selfhost_identity_is_not_reported(self):
        main = self.module()
        with (
            patch.object(main, "ANALYTICS_URL", "http://analytics:8080"),
            patch.object(main, "ANALYTICS_TOKEN", "secret"),
            patch.object(main.httpx, "AsyncClient") as client,
        ):
            await main.report_activity(main.SELFHOST_ACCOUNT)
        client.assert_not_called()

    async def test_schedule_classifies_old_account_as_app_open(self):
        main = self.module()
        actor = SimpleNamespace(
            user_id="did:privy:existing",
            email="existing@example.com",
            name="Existing Person",
            created_at=1,
        )
        with patch.object(main, "report_activity") as report:
            main.schedule_activity(actor)
            await next(iter(main.tasks))
        report.assert_awaited_once_with(
            actor.user_id, actor.email, actor.name, "app_open"
        )


if __name__ == "__main__":
    unittest.main()
