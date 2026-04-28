"""Tests for the setup_links Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient

CUSTOMER_ID = "3c90c3cc-0d44-4b50-8888-8dd25736052a"
SETUP_LINK_ID = "7f8a9b1c-2d3e-4f5a-6b7c-8d9e0f1a2b3c"


def _setup_link(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": SETUP_LINK_ID,
        "status": "active",
        "created_at": "2025-01-15T10:00:00Z",
        "url": "https://app.kapso.ai/whatsapp/setup/abc123",
        "expires_at": "2025-02-14T10:00:00Z",
        "success_redirect_url": "https://yourapp.com/whatsapp/success",
        "failure_redirect_url": "https://yourapp.com/whatsapp/failed",
        "allowed_connection_types": ["coexistence", "dedicated"],
        "provision_phone_number": False,
        "phone_number_area_code": None,
        "phone_number_country_isos": ["US"],
        "theme_config": {
            "primary_color": "#3b82f6",
            "border_color": "#d1d5db",
        },
        "whatsapp_setup_status": "pending",
        "whatsapp_setup_error": None,
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(f"/customers/{CUSTOMER_ID}/setup_links").mock(
            return_value=Response(
                200,
                json={
                    "data": [_setup_link(), _setup_link(id="other", status="used")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        result = await platform_client.setup_links.list(CUSTOMER_ID)
        assert len(result) == 2
        assert result[0].status == "active"
        assert result[1].status == "used"

    async def test_passes_filters_as_query_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get(f"/customers/{CUSTOMER_ID}/setup_links").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 10, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.setup_links.list(
            CUSTOMER_ID, status="active", per_page=10, page=2
        )
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "active"
        assert params["per_page"] == "10"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get(f"/customers/{CUSTOMER_ID}/setup_links").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.setup_links.list(CUSTOMER_ID)
        params = dict(route.calls.last.request.url.params)
        assert "status" not in params
        assert "created_after" not in params


class TestIter:
    async def test_iterates_across_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(
            f"/customers/{CUSTOMER_ID}/setup_links",
            params={"page": "1", "per_page": "1"},
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_setup_link(id="a")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get(
            f"/customers/{CUSTOMER_ID}/setup_links",
            params={"page": "2", "per_page": "1"},
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_setup_link(id="b", status="used")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        ids = [sl.id async for sl in platform_client.setup_links.iter(CUSTOMER_ID, per_page=1)]
        assert ids == ["a", "b"]


class TestCreate:
    async def test_wraps_payload_in_setup_link_key(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(f"/customers/{CUSTOMER_ID}/setup_links").mock(
            return_value=Response(201, json={"data": _setup_link()})
        )
        result = await platform_client.setup_links.create(
            CUSTOMER_ID,
            success_redirect_url="https://example.com/success",
        )
        assert result.id == SETUP_LINK_ID
        body = route.calls.last.request.read().decode()
        assert '"setup_link"' in body
        assert '"success_redirect_url"' in body

    async def test_empty_payload_allowed(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(f"/customers/{CUSTOMER_ID}/setup_links").mock(
            return_value=Response(201, json={"data": _setup_link()})
        )
        await platform_client.setup_links.create(CUSTOMER_ID)
        body = route.calls.last.request.read().decode()
        # Still wraps in setup_link key even with no fields
        assert '"setup_link"' in body


class TestUpdate:
    async def test_revoke_sends_status_field(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch(
            f"/customers/{CUSTOMER_ID}/setup_links/{SETUP_LINK_ID}"
        ).mock(
            return_value=Response(200, json={"data": _setup_link(status="revoked")})
        )
        result = await platform_client.setup_links.update(
            CUSTOMER_ID, SETUP_LINK_ID, status="revoked"
        )
        assert result.status == "revoked"
        body = route.calls.last.request.read().decode()
        assert '"setup_link"' in body
        assert '"status":"revoked"' in body

    async def test_partial_update_only_sends_provided_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch(
            f"/customers/{CUSTOMER_ID}/setup_links/{SETUP_LINK_ID}"
        ).mock(
            return_value=Response(200, json={"data": _setup_link()})
        )
        await platform_client.setup_links.update(
            CUSTOMER_ID, SETUP_LINK_ID, status="revoked"
        )
        body = route.calls.last.request.read().decode()
        assert "success_redirect_url" not in body
        assert "failure_redirect_url" not in body
