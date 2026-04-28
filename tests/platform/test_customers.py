"""Tests for the customers Platform resource (reference template)."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient


def _customer(**overrides: object) -> dict[str, object]:
    base = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Acme Corp",
        "external_customer_id": "cus_abc123",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers").mock(
            return_value=Response(
                200,
                json={
                    "data": [_customer(), _customer(id="2", name="TechStart")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        customers = await platform_client.customers.list()
        assert len(customers) == 2
        assert customers[0].name == "Acme Corp"
        assert customers[1].name == "TechStart"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/customers").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.customers.list(name_contains="acme", per_page=50, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["name_contains"] == "acme"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/customers").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.customers.list()
        params = dict(route.calls.last.request.url.params)
        assert "name_contains" not in params
        assert "external_customer_id" not in params


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_customer(id="1", name="a"), _customer(id="2", name="b")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/customers", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_customer(id="3", name="c")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        names = [c.name async for c in platform_client.customers.iter(per_page=2)]
        assert names == ["a", "b", "c"]


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers/abc-123").mock(
            return_value=Response(200, json={"data": _customer(id="abc-123", name="Acme")})
        )
        result = await platform_client.customers.get("abc-123")
        assert result.id == "abc-123"
        assert result.name == "Acme"


class TestCreate:
    async def test_wraps_payload_in_customer_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/customers").mock(
            return_value=Response(201, json={"data": _customer(name="Acme Corp")})
        )
        result = await platform_client.customers.create(name="Acme Corp", external_customer_id="cus_abc123")

        assert result.name == "Acme Corp"
        body = route.calls.last.request.read().decode()
        assert '"customer"' in body
        assert '"name":"Acme Corp"' in body
        assert '"external_customer_id":"cus_abc123"' in body

    async def test_omits_external_id_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/customers").mock(
            return_value=Response(201, json={"data": _customer(external_customer_id=None)})
        )
        await platform_client.customers.create(name="Bare")
        body = route.calls.last.request.read().decode()
        assert "external_customer_id" not in body


class TestUpdate:
    async def test_partial_update_only_sends_provided_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch("/customers/abc").mock(
            return_value=Response(200, json={"data": _customer(id="abc", name="Renamed")})
        )
        result = await platform_client.customers.update("abc", name="Renamed")
        assert result.name == "Renamed"
        body = route.calls.last.request.read().decode()
        assert '"name":"Renamed"' in body
        assert "external_customer_id" not in body


class TestDelete:
    async def test_returns_none_on_success(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.delete("/customers/abc").mock(return_value=Response(204))
        result = await platform_client.customers.delete("abc")
        assert result is None
