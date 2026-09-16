import importlib
import json
import sys
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "coffee_api"))


def load_main(monkeypatch, url="http://analytics:8080", token="secret"):
    monkeypatch.setenv("APP_MODE", "hosted")
    monkeypatch.setenv("ANALYTICS_URL", url)
    monkeypatch.setenv("ANALYTICS_TOKEN", token)
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:1")
    import src.main
    return importlib.reload(src.main)


@pytest.mark.asyncio
async def test_report_activity_sends_only_product_and_subject(monkeypatch):
    module = load_main(monkeypatch)
    seen = {}

    async def handler(request):
        seen["request"] = request
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    )
    await module.report_activity("did:privy:user")
    request = seen["request"]
    assert request.headers["authorization"] == "Bearer secret"
    assert request.url == "http://analytics:8080/v1/activity"
    assert json.loads(request.content) == {"product": "ezcoffee", "subject": "did:privy:user"}


@pytest.mark.asyncio
async def test_report_activity_is_best_effort(monkeypatch):
    module = load_main(monkeypatch)

    async def handler(_):
        raise httpx.ConnectError("offline")

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    )
    await module.report_activity("did:privy:user")


@pytest.mark.asyncio
async def test_selfhost_identity_is_not_reported(monkeypatch):
    module = load_main(monkeypatch)

    class UnexpectedClient:
        def __init__(self, **kwargs):
            raise AssertionError("analytics should not be called")

    monkeypatch.setattr(module.httpx, "AsyncClient", UnexpectedClient)
    await module.report_activity(module.SELFHOST_ACCOUNT)
