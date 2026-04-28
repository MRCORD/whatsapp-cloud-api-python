"""Tests for KapsoPlatformClient foundation: URL building, auth, unwrap, pagination, errors."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from kapso_whatsapp.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from kapso_whatsapp.platform import KapsoPlatformClient


class TestConstruction:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError):
            KapsoPlatformClient(api_key="")

    def test_default_base_url(self, platform_api_key: str) -> None:
        c = KapsoPlatformClient(api_key=platform_api_key)
        assert c.base_url == "https://api.kapso.ai/platform/v1"

    def test_strips_trailing_slash(self, platform_api_key: str) -> None:
        c = KapsoPlatformClient(api_key=platform_api_key, base_url="https://x.test/v1/")
        assert c.base_url == "https://x.test/v1"


class TestRequest:
    async def test_url_has_no_version_segment(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/customers").mock(
            return_value=Response(200, json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}})
        )
        await platform_client.request("GET", "customers")
        assert route.called
        assert route.calls.last.request.url.path == "/platform/v1/customers"

    async def test_sends_x_api_key_header(
        self,
        platform_client: KapsoPlatformClient,
        platform_api_key: str,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/customers").mock(
            return_value=Response(200, json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}})
        )
        await platform_client.request("GET", "customers")
        assert route.calls.last.request.headers["x-api-key"] == platform_api_key

    async def test_request_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers/abc").mock(
            return_value=Response(200, json={"data": {"id": "abc", "name": "X"}})
        )
        result = await platform_client.request("GET", "customers/abc")
        assert result == {"id": "abc", "name": "X"}

    async def test_request_raw_keeps_envelope(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers").mock(
            return_value=Response(200, json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}})
        )
        result = await platform_client.request_raw("GET", "customers")
        assert "meta" in result
        assert result["meta"]["page"] == 1


class TestErrorMapping:
    async def test_401_raises_authentication(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers").mock(
            return_value=Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            await platform_client.request("GET", "customers")

    async def test_404_raises_not_found(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers/missing").mock(
            return_value=Response(404, json={"error": "Not found"})
        )
        with pytest.raises(NotFoundError):
            await platform_client.request("GET", "customers/missing")

    async def test_422_raises_validation(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post("/customers").mock(
            return_value=Response(422, json={"error": "name is required"})
        )
        with pytest.raises(ValidationError):
            await platform_client.request("POST", "customers", json={"customer": {}})

    async def test_429_raises_rate_limit_with_retry_after(
        self, platform_api_key: str, mock_platform_api: respx.MockRouter
    ) -> None:
        client = KapsoPlatformClient(api_key=platform_api_key, max_retries=0)
        mock_platform_api.get("/customers").mock(
            return_value=Response(429, json={"error": "rate limited"}, headers={"Retry-After": "7"})
        )
        with pytest.raises(RateLimitError) as exc:
            await client.request("GET", "customers")
        assert exc.value.retry_after == 7


class TestPagination:
    async def test_paginate_walks_all_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/customers", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [{"id": "3", "name": "c"}],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        ids = [row["id"] async for row in platform_client.paginate("customers", per_page=2)]
        assert ids == ["1", "2", "3"]

    async def test_paginate_stops_at_max_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/customers").mock(
            return_value=Response(
                200,
                json={
                    "data": [{"id": "x"}],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 999, "total_count": 999},
                },
            )
        )
        rows = [r async for r in platform_client.paginate("customers", per_page=1, max_pages=1)]
        assert len(rows) == 1
