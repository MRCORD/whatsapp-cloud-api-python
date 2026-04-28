"""Tests for the WebhookDeliveries Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.webhook_deliveries import WebhookDeliveriesResource


def _delivery(**overrides: object) -> dict[str, object]:
    base = {
        "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
        "event": "whatsapp.message.received",
        "status": "delivered",
        "attempt_count": 1,
        "created_at": "2025-01-15T10:00:00Z",
        "response_status": 200,
        "delivered_at": "2025-01-15T10:00:01Z",
        "failed_at": None,
        "last_attempt_at": "2025-01-15T10:00:01Z",
        "webhook_id": "aaaabbbb-0000-0000-0000-000000000001",
        "webhook_url": "https://api.acme.com/webhooks/whatsapp",
        "whatsapp_config_id": "ccccdddd-0000-0000-0000-000000000002",
        "phone_number_id": "1234567890",
        "conversation_phone_number": "+15551234567",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/webhook_deliveries").mock(
            return_value=Response(
                200,
                json={
                    "data": [_delivery(), _delivery(id="2", status="failed")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        resource = WebhookDeliveriesResource(platform_client)
        deliveries = await resource.list()
        assert len(deliveries) == 2
        assert deliveries[0].status == "delivered"
        assert deliveries[1].status == "failed"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/webhook_deliveries").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = WebhookDeliveriesResource(platform_client)
        await resource.list(
            status="failed",
            event="whatsapp.message.received",
            period="7d",
            errors_only=True,
            per_page=50,
            page=2,
        )
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "failed"
        assert params["event"] == "whatsapp.message.received"
        assert params["period"] == "7d"
        assert params["errors_only"] == "true"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/webhook_deliveries").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = WebhookDeliveriesResource(platform_client)
        await resource.list()
        params = dict(route.calls.last.request.url.params)
        assert "status" not in params
        assert "event" not in params
        assert "webhook_id" not in params
        assert "errors_only" not in params
        assert "period" not in params

    async def test_model_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/webhook_deliveries").mock(
            return_value=Response(
                200,
                json={
                    "data": [_delivery()],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 1},
                },
            )
        )
        resource = WebhookDeliveriesResource(platform_client)
        deliveries = await resource.list()
        d = deliveries[0]
        assert d.id == "3c90c3cc-0d44-4b50-8888-8dd25736052a"
        assert d.event == "whatsapp.message.received"
        assert d.webhook_url == "https://api.acme.com/webhooks/whatsapp"
        assert d.attempt_count == 1
        assert d.response_status == 200


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/webhook_deliveries", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_delivery(id="1"), _delivery(id="2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/webhook_deliveries", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_delivery(id="3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        resource = WebhookDeliveriesResource(platform_client)
        ids = [d.id async for d in resource.iter(per_page=2)]
        assert ids == ["1", "2", "3"]
