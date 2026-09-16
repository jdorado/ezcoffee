import json
import sys
import unittest
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
            await main.report_activity("did:privy:user")

        request = seen["request"]
        self.assertEqual(request.headers["authorization"], "Bearer secret")
        self.assertEqual(str(request.url), "http://analytics:8080/v1/activity")
        self.assertEqual(
            json.loads(request.content),
            {"product": "ezcoffee", "subject": "did:privy:user"},
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


if __name__ == "__main__":
    unittest.main()
