"""Tests for the WhatsApp Flows Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.whatsapp_flows import (
    DataEndpoint,
    EncryptionResult,
    FlowVersion,
    FunctionInvocations,
    FunctionLogs,
    RegisteredDataEndpoint,
    WhatsAppFlow,
)

FLOW_ID = "3c90c3cc-0d44-4b50-8888-8dd25736052a"
VERSION_ID = "4d01d4dd-e35c-52e5-9999-9ee36847163b"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _flow(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": FLOW_ID,
        "meta_flow_id": "meta-123",
        "name": "My Flow",
        "status": "draft",
        "created_at": "2023-11-07T05:31:56Z",
        "updated_at": "2023-11-07T05:31:56Z",
        "json_version": "3.0",
        "data_api_version": "3.0",
        "business_account_id": "waba-abc",
        "preview_url": "https://preview.example.com",
        "published_at": None,
        "last_synced_at": "2023-11-07T05:31:56Z",
        "data_endpoint_function_id": None,
        "phone_number_id": "phone-999",
        "data_endpoint_url": None,
        "has_data_endpoint": False,
        "flows_encryption_configured": False,
    }
    base.update(overrides)
    return base


def _version(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": VERSION_ID,
        "version_label": "v1",
        "status": "draft",
        "created_at": "2023-11-07T05:31:56Z",
        "updated_at": "2023-11-07T05:31:56Z",
        "flow_json_sha": "abc123",
        "published_at": None,
        "validation_errors": [],
        "flow_json": {"version": "3.0", "screens": []},
    }
    base.update(overrides)
    return base


def _data_endpoint(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "function_id": FLOW_ID,
        "function_name": "my-flow-fn",
        "status": "deployed",
        "endpoint_url": "https://my-flow-fn.workers.dev",
        "last_deployed_at": "2023-11-07T05:31:56Z",
        "code": "export default { async fetch(req) { return new Response('ok'); } }",
    }
    base.update(overrides)
    return base


def _paginated(items: list[object], *, page: int = 1, total_pages: int = 1) -> dict[str, object]:
    return {
        "data": items,
        "meta": {
            "page": page,
            "per_page": len(items) or 20,
            "total_pages": total_pages,
            "total_count": len(items),
        },
    }


# ---------------------------------------------------------------------------
# List flows
# ---------------------------------------------------------------------------


class TestListFlows:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/flows").mock(
            return_value=Response(200, json=_paginated([_flow(), _flow(id="2", name="Other")]))
        )
        flows = await platform_client.whatsapp_flows.list()
        assert len(flows) == 2
        assert isinstance(flows[0], WhatsAppFlow)
        assert flows[0].name == "My Flow"
        assert flows[1].name == "Other"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/flows").mock(
            return_value=Response(200, json=_paginated([]))
        )
        await platform_client.whatsapp_flows.list(
            status="draft", name_contains="onboard", per_page=50, page=2
        )
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "draft"
        assert params["name_contains"] == "onboard"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/flows").mock(
            return_value=Response(200, json=_paginated([]))
        )
        await platform_client.whatsapp_flows.list()
        params = dict(route.calls.last.request.url.params)
        assert "status" not in params
        assert "business_account_id" not in params
        assert "name_contains" not in params


# ---------------------------------------------------------------------------
# Iter flows
# ---------------------------------------------------------------------------


class TestIterFlows:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/flows", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_flow(id="1", name="a"), _flow(id="2", name="b")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/whatsapp/flows", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_flow(id="3", name="c")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        names = [f.name async for f in platform_client.whatsapp_flows.iter(per_page=2)]
        assert names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Get flow
# ---------------------------------------------------------------------------


class TestGetFlow:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}").mock(
            return_value=Response(200, json={"data": _flow(name="My Flow")})
        )
        result = await platform_client.whatsapp_flows.get(FLOW_ID)
        assert isinstance(result, WhatsAppFlow)
        assert result.id == FLOW_ID
        assert result.name == "My Flow"


# ---------------------------------------------------------------------------
# Create flow
# ---------------------------------------------------------------------------


class TestCreateFlow:
    async def test_sends_phone_number_id(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/flows").mock(
            return_value=Response(201, json={"data": _flow()})
        )
        result = await platform_client.whatsapp_flows.create(phone_number_id="phone-999")
        assert isinstance(result, WhatsAppFlow)
        body = route.calls.last.request.read().decode()
        assert '"phone_number_id":"phone-999"' in body

    async def test_optional_fields_included_when_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/flows").mock(
            return_value=Response(201, json={"data": _flow(name="My Flow", status="published")})
        )
        await platform_client.whatsapp_flows.create(
            phone_number_id="phone-999",
            name="My Flow",
            flow_json={"version": "3.0"},
            publish=True,
        )
        body = route.calls.last.request.read().decode()
        assert '"name":"My Flow"' in body
        assert '"flow_json"' in body
        assert '"publish":true' in body

    async def test_optional_fields_omitted_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/flows").mock(
            return_value=Response(201, json={"data": _flow()})
        )
        await platform_client.whatsapp_flows.create(phone_number_id="phone-999")
        body = route.calls.last.request.read().decode()
        assert "name" not in body
        assert "flow_json" not in body
        assert "publish" not in body


# ---------------------------------------------------------------------------
# Publish flow
# ---------------------------------------------------------------------------


class TestPublishFlow:
    async def test_posts_to_correct_url(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/publish").mock(
            return_value=Response(200, json={"data": _flow(status="published")})
        )
        result = await platform_client.whatsapp_flows.publish(FLOW_ID)
        assert isinstance(result, WhatsAppFlow)
        assert route.calls.call_count == 1

    async def test_passes_optional_phone_number_id(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/publish").mock(
            return_value=Response(200, json={"data": _flow()})
        )
        await platform_client.whatsapp_flows.publish(FLOW_ID, phone_number_id="phone-555")
        body = route.calls.last.request.read().decode()
        assert '"phone_number_id":"phone-555"' in body

    async def test_sends_empty_body_when_no_phone(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/publish").mock(
            return_value=Response(200, json={"data": _flow()})
        )
        await platform_client.whatsapp_flows.publish(FLOW_ID)
        body = route.calls.last.request.read().decode()
        assert "phone_number_id" not in body


# ---------------------------------------------------------------------------
# Setup encryption
# ---------------------------------------------------------------------------


class TestSetupEncryption:
    async def test_returns_encryption_result(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/setup_encryption").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "status": "success",
                        "message": "Encryption configured",
                        "flows_encryption_configured": True,
                    }
                },
            )
        )
        result = await platform_client.whatsapp_flows.setup_encryption(FLOW_ID)
        assert isinstance(result, EncryptionResult)
        assert result.status == "success"
        assert result.flows_encryption_configured is True

    async def test_passes_phone_number_id(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/setup_encryption").mock(
            return_value=Response(
                200,
                json={"data": {"status": "success", "flows_encryption_configured": True}},
            )
        )
        await platform_client.whatsapp_flows.setup_encryption(FLOW_ID, phone_number_id="phone-777")
        body = route.calls.last.request.read().decode()
        assert '"phone_number_id":"phone-777"' in body


# ---------------------------------------------------------------------------
# List versions
# ---------------------------------------------------------------------------


class TestListVersions:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/versions").mock(
            return_value=Response(
                200, json=_paginated([_version(), _version(id="v2", version_label="v2")])
            )
        )
        versions = await platform_client.whatsapp_flows.list_versions(FLOW_ID)
        assert len(versions) == 2
        assert isinstance(versions[0], FlowVersion)
        assert versions[0].version_label == "v1"
        assert versions[1].version_label == "v2"

    async def test_passes_pagination_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/versions").mock(
            return_value=Response(200, json=_paginated([]))
        )
        await platform_client.whatsapp_flows.list_versions(FLOW_ID, per_page=10, page=3)
        params = dict(route.calls.last.request.url.params)
        assert params["per_page"] == "10"
        assert params["page"] == "3"


# ---------------------------------------------------------------------------
# Iter versions
# ---------------------------------------------------------------------------


class TestIterVersions:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(
            f"/whatsapp/flows/{FLOW_ID}/versions", params={"page": "1", "per_page": "1"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_version(id="v1", version_label="v1")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get(
            f"/whatsapp/flows/{FLOW_ID}/versions", params={"page": "2", "per_page": "1"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_version(id="v2", version_label="v2")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        labels = [
            v.version_label
            async for v in platform_client.whatsapp_flows.iter_versions(FLOW_ID, per_page=1)
        ]
        assert labels == ["v1", "v2"]


# ---------------------------------------------------------------------------
# Get version
# ---------------------------------------------------------------------------


class TestGetVersion:
    async def test_includes_flow_json(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(
            f"/whatsapp/flows/{FLOW_ID}/versions/{VERSION_ID}"
        ).mock(
            return_value=Response(200, json={"data": _version()})
        )
        result = await platform_client.whatsapp_flows.get_version(FLOW_ID, VERSION_ID)
        assert isinstance(result, FlowVersion)
        assert result.id == VERSION_ID
        assert result.flow_json is not None


# ---------------------------------------------------------------------------
# Create version
# ---------------------------------------------------------------------------


class TestCreateVersion:
    async def test_sends_flow_json(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/versions").mock(
            return_value=Response(201, json={"data": _version()})
        )
        flow_def = {"version": "3.0", "screens": []}
        result = await platform_client.whatsapp_flows.create_version(
            FLOW_ID, flow_json=flow_def
        )
        assert isinstance(result, FlowVersion)
        body = route.calls.last.request.read().decode()
        assert '"flow_json"' in body
        assert "3.0" in body

    async def test_optional_phone_number_id_included_when_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/versions").mock(
            return_value=Response(201, json={"data": _version()})
        )
        await platform_client.whatsapp_flows.create_version(
            FLOW_ID,
            flow_json={"version": "3.0"},
            phone_number_id="phone-123",
        )
        body = route.calls.last.request.read().decode()
        assert '"phone_number_id":"phone-123"' in body

    async def test_omits_phone_number_id_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/versions").mock(
            return_value=Response(201, json={"data": _version()})
        )
        await platform_client.whatsapp_flows.create_version(
            FLOW_ID, flow_json={"version": "3.0"}
        )
        body = route.calls.last.request.read().decode()
        assert "phone_number_id" not in body


# ---------------------------------------------------------------------------
# Get data endpoint
# ---------------------------------------------------------------------------


class TestGetDataEndpoint:
    async def test_returns_data_endpoint(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/data_endpoint").mock(
            return_value=Response(200, json={"data": _data_endpoint()})
        )
        result = await platform_client.whatsapp_flows.get_data_endpoint(FLOW_ID)
        assert isinstance(result, DataEndpoint)
        assert result.function_id == FLOW_ID
        assert result.status == "deployed"


# ---------------------------------------------------------------------------
# Upsert data endpoint
# ---------------------------------------------------------------------------


class TestUpsertDataEndpoint:
    async def test_sends_code(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/flows/{FLOW_ID}/data_endpoint").mock(
            return_value=Response(200, json={"data": _data_endpoint()})
        )
        worker_code = "export default { async fetch(req) { return new Response('ok'); } }"
        result = await platform_client.whatsapp_flows.upsert_data_endpoint(
            FLOW_ID, code=worker_code
        )
        assert isinstance(result, DataEndpoint)
        body = route.calls.last.request.read().decode()
        assert '"code"' in body


# ---------------------------------------------------------------------------
# Deploy data endpoint
# ---------------------------------------------------------------------------


class TestDeployDataEndpoint:
    async def test_posts_to_correct_url(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(
            f"/whatsapp/flows/{FLOW_ID}/data_endpoint/deploy"
        ).mock(return_value=Response(200, json={"data": _data_endpoint(status="deployed")}))
        result = await platform_client.whatsapp_flows.deploy_data_endpoint(FLOW_ID)
        assert isinstance(result, DataEndpoint)
        assert route.calls.call_count == 1


# ---------------------------------------------------------------------------
# Register data endpoint with Meta
# ---------------------------------------------------------------------------


class TestRegisterDataEndpointWithMeta:
    async def test_returns_registered_endpoint(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post(
            f"/whatsapp/flows/{FLOW_ID}/data_endpoint/register"
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        **_data_endpoint(),
                        "flow_id": FLOW_ID,
                        "flow_data_endpoint_function_id": FLOW_ID,
                        "flow_has_encryption": True,
                    }
                },
            )
        )
        result = await platform_client.whatsapp_flows.register_data_endpoint_with_meta(FLOW_ID)
        assert isinstance(result, RegisteredDataEndpoint)
        assert result.flow_has_encryption is True
        assert result.flow_id == FLOW_ID


# ---------------------------------------------------------------------------
# Get function logs
# ---------------------------------------------------------------------------


class TestGetFunctionLogs:
    async def test_returns_function_logs(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/function_logs").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "function_id": FLOW_ID,
                        "function_name": "my-fn",
                        "logs": [
                            {
                                "level": "info",
                                "message": "Request received",
                                "logged_at": "2023-11-07T05:31:56Z",
                                "stack": None,
                                "cf_ray": "abc123",
                                "outcome": "ok",
                            }
                        ],
                    }
                },
            )
        )
        result = await platform_client.whatsapp_flows.get_function_logs(FLOW_ID)
        assert isinstance(result, FunctionLogs)
        assert len(result.logs) == 1
        assert result.logs[0].level == "info"

    async def test_passes_limit_param(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/function_logs").mock(
            return_value=Response(
                200,
                json={"data": {"function_id": FLOW_ID, "function_name": "fn", "logs": []}},
            )
        )
        await platform_client.whatsapp_flows.get_function_logs(FLOW_ID, limit=5)
        params = dict(route.calls.last.request.url.params)
        assert params["limit"] == "5"


# ---------------------------------------------------------------------------
# Get function invocations
# ---------------------------------------------------------------------------


class TestGetFunctionInvocations:
    async def test_returns_function_invocations(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/function_invocations").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "function_id": FLOW_ID,
                        "function_name": "my-fn",
                        "invocations": [
                            {
                                "id": "inv-1",
                                "status_code": 200,
                                "duration_ms": 45,
                                "request_body": {},
                                "response_body": {"result": "ok"},
                                "error_message": None,
                                "cf_ray": "ray123",
                                "created_at": "2023-11-07T05:31:56Z",
                            }
                        ],
                    }
                },
            )
        )
        result = await platform_client.whatsapp_flows.get_function_invocations(FLOW_ID)
        assert isinstance(result, FunctionInvocations)
        assert len(result.invocations) == 1
        assert result.invocations[0].status_code == 200

    async def test_passes_status_filter(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/function_invocations").mock(
            return_value=Response(
                200,
                json={"data": {"function_id": FLOW_ID, "function_name": "fn", "invocations": []}},
            )
        )
        await platform_client.whatsapp_flows.get_function_invocations(
            FLOW_ID, status="failed", limit=5
        )
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "failed"
        assert params["limit"] == "5"

    async def test_omits_status_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get(f"/whatsapp/flows/{FLOW_ID}/function_invocations").mock(
            return_value=Response(
                200,
                json={"data": {"function_id": FLOW_ID, "function_name": "fn", "invocations": []}},
            )
        )
        await platform_client.whatsapp_flows.get_function_invocations(FLOW_ID)
        params = dict(route.calls.last.request.url.params)
        assert "status" not in params
