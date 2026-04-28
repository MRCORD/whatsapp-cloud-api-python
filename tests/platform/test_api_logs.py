"""Tests for the ApiLogs Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.api_logs import ApiLogsResource


def _log(**overrides: object) -> dict[str, object]:
    base = {
        "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
        "endpoint": "/platform/v1/customers",
        "http_method": "GET",
        "response_status": 200,
        "response_time_ms": 45,
        "created_at": "2025-01-15T10:00:00Z",
        "ip_address": "192.0.2.1",
        "error_message": None,
        "api_key_id": "key-uuid-0001",
        "api_key_name": "Production Key",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/api_logs").mock(
            return_value=Response(
                200,
                json={
                    "data": [_log(), _log(id="2", http_method="POST", response_status=422)],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        resource = ApiLogsResource(platform_client)
        logs = await resource.list()
        assert len(logs) == 2
        assert logs[0].http_method == "GET"
        assert logs[1].response_status == 422

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/api_logs").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = ApiLogsResource(platform_client)
        await resource.list(
            endpoint="/customers",
            status_code=200,
            errors_only=False,
            period="7d",
            per_page=50,
            page=2,
        )
        params = dict(route.calls.last.request.url.params)
        assert params["endpoint"] == "/customers"
        assert params["status_code"] == "200"
        assert params["errors_only"] == "false"
        assert params["period"] == "7d"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/api_logs").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        resource = ApiLogsResource(platform_client)
        await resource.list()
        params = dict(route.calls.last.request.url.params)
        assert "endpoint" not in params
        assert "status_code" not in params
        assert "errors_only" not in params
        assert "period" not in params

    async def test_model_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/api_logs").mock(
            return_value=Response(
                200,
                json={
                    "data": [_log()],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 1},
                },
            )
        )
        resource = ApiLogsResource(platform_client)
        logs = await resource.list()
        entry = logs[0]
        assert entry.id == "3c90c3cc-0d44-4b50-8888-8dd25736052a"
        assert entry.endpoint == "/platform/v1/customers"
        assert entry.response_time_ms == 45
        assert entry.api_key_name == "Production Key"
        assert entry.error_message is None


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/api_logs", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_log(id="1"), _log(id="2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/api_logs", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_log(id="3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        resource = ApiLogsResource(platform_client)
        ids = [entry.id async for entry in resource.iter(per_page=2)]
        assert ids == ["1", "2", "3"]


class TestDocExampleValidates:
    """Regression guard: doc example from docs.kapso.ai/api/platform/v1/api-logs/list-api-logs
    must remain parseable by ApiLog without modification."""

    def test_api_log_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.api_logs import ApiLog

        example = {
            "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "endpoint": "<string>",
            "http_method": "<string>",
            "response_status": 123,
            "response_time_ms": 123,
            "created_at": "2023-11-07T05:31:56Z",
            "ip_address": "<string>",
            "error_message": "<string>",
            "api_key_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "api_key_name": "<string>",
        }
        ApiLog.model_validate(example)  # raises if model gets stricter than docs
