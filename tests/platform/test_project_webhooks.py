"""Tests for the ProjectWebhooks Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.project_webhooks import ProjectWebhooksResource


def _webhook(**overrides: object) -> dict[str, object]:
    base = {
        "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
        "url": "https://api.acme.com/webhooks/whatsapp",
        "kind": "kapso",
        "events": ["whatsapp.phone_number.created"],
        "active": True,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "project_id": "1d6ca0a3-91c2-4f13-8a94-28ddb0d5f2f3",
        "phone_number_id": None,
        "secret_key": "wh_sec_test",
        "headers": {},
        "buffer_enabled": False,
        "buffer_window_seconds": None,
        "max_buffer_size": None,
        "buffer_events": [],
        "inactivity_minutes": None,
        "payload_version": None,
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/webhooks").mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(), _webhook(id="2", url="https://other.example.com/wh")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        resource = ProjectWebhooksResource(platform_client)
        webhooks = await resource.list()
        assert len(webhooks) == 2
        assert webhooks[0].url == "https://api.acme.com/webhooks/whatsapp"
        assert webhooks[1].id == "2"

    async def test_passes_kind_filter_as_query_param(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/webhooks").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.list(kind="kapso", per_page=10, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["kind"] == "kapso"
        assert params["per_page"] == "10"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/webhooks").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.list()
        params = dict(route.calls.last.request.url.params)
        assert "kind" not in params


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/webhooks", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(id="1"), _webhook(id="2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/whatsapp/webhooks", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_webhook(id="3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        resource = ProjectWebhooksResource(platform_client)
        ids = [w.id async for w in resource.iter(per_page=2)]
        assert ids == ["1", "2", "3"]


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/webhooks/abc-123").mock(
            return_value=Response(200, json={"data": _webhook(id="abc-123")})
        )
        resource = ProjectWebhooksResource(platform_client)
        result = await resource.get("abc-123")
        assert result.id == "abc-123"
        assert result.kind == "kapso"


class TestCreate:
    async def test_wraps_payload_in_whatsapp_webhook_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/webhooks").mock(
            return_value=Response(201, json={"data": _webhook()})
        )
        resource = ProjectWebhooksResource(platform_client)
        result = await resource.create(
            url="https://api.acme.com/webhooks/whatsapp",
            events=["whatsapp.phone_number.created"],
            secret_key="wh_sec_test",
        )
        assert result.url == "https://api.acme.com/webhooks/whatsapp"
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"url"' in body
        assert '"events"' in body
        assert '"secret_key":"wh_sec_test"' in body

    async def test_omits_optional_fields_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/webhooks").mock(
            return_value=Response(201, json={"data": _webhook()})
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.create(
            url="https://api.acme.com/webhooks/whatsapp",
            events=["whatsapp.phone_number.created"],
        )
        body = route.calls.last.request.read().decode()
        assert "secret_key" not in body
        assert "phone_number_id" not in body


class TestUpdate:
    async def test_partial_update_only_sends_provided_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch("/whatsapp/webhooks/abc").mock(
            return_value=Response(200, json={"data": _webhook(id="abc", buffer_enabled=True)})
        )
        resource = ProjectWebhooksResource(platform_client)
        result = await resource.update("abc", buffer_enabled=True, buffer_window_seconds=5)
        assert result.buffer_enabled is True
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"buffer_enabled":true' in body
        assert "url" not in body

    async def test_wraps_payload_in_whatsapp_webhook_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch("/whatsapp/webhooks/xyz").mock(
            return_value=Response(200, json={"data": _webhook(id="xyz")})
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.update("xyz", active=False)
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_webhook"' in body
        assert '"active":false' in body


class TestDelete:
    async def test_returns_none_on_success(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.delete("/whatsapp/webhooks/abc").mock(return_value=Response(204))
        resource = ProjectWebhooksResource(platform_client)
        result = await resource.delete("abc")
        assert result is None


class TestTest:
    async def test_sends_test_payload_and_returns_result(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post("/whatsapp/webhooks/abc/test").mock(
            return_value=Response(200, json={"data": {"success": True}})
        )
        resource = ProjectWebhooksResource(platform_client)
        result = await resource.test("abc")
        assert result.success is True

    async def test_sends_event_type_when_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/webhooks/abc/test").mock(
            return_value=Response(200, json={"data": {"success": True}})
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.test("abc", event_type="whatsapp.phone_number.created")
        body = route.calls.last.request.read().decode()
        assert "whatsapp.phone_number.created" in body

    async def test_sends_empty_body_when_no_event_type(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/webhooks/abc/test").mock(
            return_value=Response(200, json={"data": {"success": True}})
        )
        resource = ProjectWebhooksResource(platform_client)
        await resource.test("abc")
        body = route.calls.last.request.read().decode()
        assert "event_type" not in body


class TestDocExampleValidates:
    """Regression guard: doc example from
    docs.kapso.ai/api/platform/v1/webhooks/get-project-webhook
    must remain parseable by ProjectWebhook without modification."""

    def test_project_webhook_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.project_webhooks import ProjectWebhook

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
        ProjectWebhook.model_validate(example)  # raises if model gets stricter than docs
