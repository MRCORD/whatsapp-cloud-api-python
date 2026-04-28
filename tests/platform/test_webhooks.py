"""Tests for the Webhooks Platform resource (phone-number-scoped)."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.webhooks import WebhooksResource

_PHONE_ID = "1234567890"


def _webhook(**overrides: object) -> dict[str, object]:
    base = {
        "id": "9e8d7c6b-5a4f-3e2d-1c0b-9a8f7e6d5c4b",
        "url": "https://api.acme.com/webhooks/whatsapp",
        "kind": "kapso",
        "events": ["whatsapp.message.received", "whatsapp.message.sent"],
        "active": True,
        "created_at": "2025-07-14T15:00:00Z",
        "updated_at": "2025-07-14T15:00:00Z",
        "project_id": "1d6ca0a3-91c2-4f13-8a94-28ddb0d5f2f3",
        "phone_number_id": _PHONE_ID,
        "secret_key": "wh_sec_3kfj9dmfkg8s2",
        "headers": {},
        "buffer_enabled": False,
        "buffer_window_seconds": None,
        "max_buffer_size": None,
        "buffer_events": [],
        "inactivity_minutes": 60,
        "payload_version": None,
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks").mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(), _webhook(id="2")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        resource = WebhooksResource(platform_client)
        webhooks = await resource.list(_PHONE_ID)
        assert len(webhooks) == 2
        assert webhooks[0].phone_number_id == _PHONE_ID

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = WebhooksResource(platform_client)
        await resource.list(
            _PHONE_ID,
            kind="kapso",
            url_contains="acme",
            per_page=50,
            page=3,
        )
        params = dict(route.calls.last.request.url.params)
        assert params["kind"] == "kapso"
        assert params["url_contains"] == "acme"
        assert params["per_page"] == "50"
        assert params["page"] == "3"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = WebhooksResource(platform_client)
        await resource.list(_PHONE_ID)
        params = dict(route.calls.last.request.url.params)
        assert "kind" not in params
        assert "url_contains" not in params
        assert "active" not in params


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        base_path = f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks"
        mock_platform_api.get(base_path, params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(id="1"), _webhook(id="2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get(base_path, params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(id="3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        resource = WebhooksResource(platform_client)
        ids = [w.id async for w in resource.iter(_PHONE_ID, per_page=2)]
        assert ids == ["1", "2", "3"]


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        wh_id = "9e8d7c6b-5a4f-3e2d-1c0b-9a8f7e6d5c4b"
        mock_platform_api.get(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks/{wh_id}").mock(
            return_value=Response(200, json={"data": _webhook(id=wh_id)})
        )
        resource = WebhooksResource(platform_client)
        result = await resource.get(_PHONE_ID, wh_id)
        assert result.id == wh_id
        assert result.phone_number_id == _PHONE_ID


class TestCreate:
    async def test_wraps_payload_in_whatsapp_webhook_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks").mock(
            return_value=Response(201, json={"data": _webhook()})
        )
        resource = WebhooksResource(platform_client)
        result = await resource.create(
            _PHONE_ID,
            url="https://api.acme.com/webhooks/whatsapp",
            events=["whatsapp.message.received", "whatsapp.message.sent"],
            secret_key="wh_sec_3kfj9dmfkg8s2",
            active=True,
        )
        assert result.url == "https://api.acme.com/webhooks/whatsapp"
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"url"' in body
        assert '"active":true' in body

    async def test_omits_optional_fields_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks").mock(
            return_value=Response(201, json={"data": _webhook()})
        )
        resource = WebhooksResource(platform_client)
        await resource.create(
            _PHONE_ID,
            url="https://api.acme.com/webhooks/whatsapp",
            events=["whatsapp.message.received"],
        )
        body = route.calls.last.request.read().decode()
        assert "secret_key" not in body
        assert "buffer_enabled" not in body


class TestUpdate:
    async def test_partial_update_only_sends_provided_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        wh_id = "9e8d7c6b-5a4f-3e2d-1c0b-9a8f7e6d5c4b"
        route = mock_platform_api.patch(
            f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks/{wh_id}"
        ).mock(
            return_value=Response(200, json={"data": _webhook(id=wh_id, buffer_enabled=True)})
        )
        resource = WebhooksResource(platform_client)
        result = await resource.update(
            _PHONE_ID, wh_id, buffer_enabled=True, buffer_window_seconds=5, max_buffer_size=20
        )
        assert result.buffer_enabled is True
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"buffer_enabled":true' in body
        assert "url" not in body

    async def test_wraps_in_whatsapp_webhook_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        wh_id = "9e8d7c6b-5a4f-3e2d-1c0b-9a8f7e6d5c4b"
        route = mock_platform_api.patch(
            f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks/{wh_id}"
        ).mock(return_value=Response(200, json={"data": _webhook(id=wh_id, active=False)}))
        resource = WebhooksResource(platform_client)
        await resource.update(_PHONE_ID, wh_id, active=False)
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"active":false' in body


class TestDelete:
    async def test_returns_none_on_success(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        wh_id = "9e8d7c6b-5a4f-3e2d-1c0b-9a8f7e6d5c4b"
        mock_platform_api.delete(
            f"/whatsapp/phone_numbers/{_PHONE_ID}/webhooks/{wh_id}"
        ).mock(return_value=Response(204))
        resource = WebhooksResource(platform_client)
        result = await resource.delete(_PHONE_ID, wh_id)
        assert result is None


class TestDocExampleValidates:
    """Regression guard: doc example from docs.kapso.ai/api/platform/v1/webhooks/get-webhook
    must remain parseable by Webhook without modification."""

    def test_webhook_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.webhooks import Webhook

        example = {
            "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "url": "<string>",
            "kind": "kapso",
            "events": ["<string>"],
            "active": True,
            "created_at": "2023-11-07T05:31:56Z",
            "updated_at": "2023-11-07T05:31:56Z",
            "project_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "phone_number_id": "<string>",
            "secret_key": "<string>",
            "headers": {},
            "buffer_enabled": True,
            "buffer_window_seconds": 123,
            "max_buffer_size": 123,
            "buffer_events": ["<string>"],
            "inactivity_minutes": 123,
            "payload_version": "<string>",
        }
        Webhook.model_validate(example)  # raises if model gets stricter than docs
