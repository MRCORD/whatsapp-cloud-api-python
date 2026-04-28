"""
WhatsApp Flows resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/whatsapp-flows/*

Sub-resources:
  * Flows — list / iter / get / create / publish / setup_encryption
  * Versions — list_versions / iter_versions / get_version / create_version
  * Data endpoint — get_data_endpoint / upsert_data_endpoint /
                    deploy_data_endpoint / register_data_endpoint_with_meta
  * Function observability — get_function_logs / get_function_invocations
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class WhatsAppFlow(BaseModel):
    id: str
    meta_flow_id: str | None = None
    name: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    json_version: str | None = None
    data_api_version: str | None = None
    business_account_id: str | None = None
    preview_url: str | None = None
    published_at: str | None = None
    last_synced_at: str | None = None
    data_endpoint_function_id: str | None = None
    phone_number_id: str | None = None
    data_endpoint_url: str | None = None
    has_data_endpoint: bool | None = None
    flows_encryption_configured: bool | None = None


class EncryptionResult(BaseModel):
    status: str | None = None
    message: str | None = None
    flows_encryption_configured: bool | None = None


class FlowVersion(BaseModel):
    id: str
    version_label: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    flow_json_sha: str | None = None
    published_at: str | None = None
    validation_errors: list[dict[str, Any]] | None = None
    flow_json: dict[str, Any] | None = None


class DataEndpoint(BaseModel):
    function_id: str | None = None
    function_name: str | None = None
    status: str | None = None
    endpoint_url: str | None = None
    last_deployed_at: str | None = None
    code: str | None = None


class RegisteredDataEndpoint(BaseModel):
    function_id: str | None = None
    function_name: str | None = None
    status: str | None = None
    endpoint_url: str | None = None
    last_deployed_at: str | None = None
    code: str | None = None
    flow_id: str | None = None
    flow_data_endpoint_function_id: str | None = None
    flow_has_encryption: bool | None = None


class FunctionLogEntry(BaseModel):
    level: str | None = None
    message: str | None = None
    logged_at: str | None = None
    stack: str | None = None
    cf_ray: str | None = None
    outcome: str | None = None


class FunctionLogs(BaseModel):
    function_id: str | None = None
    function_name: str | None = None
    logs: list[FunctionLogEntry] = []


class FunctionInvocation(BaseModel):
    id: str | None = None
    status_code: int | None = None
    duration_ms: int | None = None
    request_body: dict[str, Any] | None = None
    response_body: dict[str, Any] | None = None
    error_message: str | None = None
    cf_ray: str | None = None
    created_at: str | None = None


class FunctionInvocations(BaseModel):
    function_id: str | None = None
    function_name: str | None = None
    invocations: list[FunctionInvocation] = []


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class WhatsAppFlowsResource(PlatformBaseResource):
    """Manage WhatsApp Flows on your Kapso project."""

    # ------------------------------------------------------------------ #
    # Flows                                                                #
    # ------------------------------------------------------------------ #

    async def list(
        self,
        *,
        status: str | None = None,
        business_account_id: str | None = None,
        phone_number_id: str | None = None,
        name_contains: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[WhatsAppFlow]:
        """List flows (single page). For full iteration use `iter()`."""
        params = _filters(
            status=status,
            business_account_id=business_account_id,
            phone_number_id=phone_number_id,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/flows", params=params)
        return [WhatsAppFlow.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        status: str | None = None,
        business_account_id: str | None = None,
        phone_number_id: str | None = None,
        name_contains: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[WhatsAppFlow]:
        """Async iterator over every flow matching the filters."""
        params = _filters(
            status=status,
            business_account_id=business_account_id,
            phone_number_id=phone_number_id,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate(
            "whatsapp/flows", params=params, per_page=per_page
        ):
            yield WhatsAppFlow.model_validate(row)

    async def get(self, flow_id: str) -> WhatsAppFlow:
        """Fetch a single flow by id."""
        row = await self._request("GET", f"whatsapp/flows/{flow_id}")
        return WhatsAppFlow.model_validate(row)

    async def create(
        self,
        *,
        phone_number_id: str,
        name: str | None = None,
        flow_json: dict[str, Any] | None = None,
        publish: bool = False,
    ) -> WhatsAppFlow:
        """Create a new WhatsApp Flow (draft by default)."""
        payload: dict[str, Any] = {"phone_number_id": phone_number_id}
        if name is not None:
            payload["name"] = name
        if flow_json is not None:
            payload["flow_json"] = flow_json
        if publish:
            payload["publish"] = publish
        row = await self._request("POST", "whatsapp/flows", json=payload)
        return WhatsAppFlow.model_validate(row)

    async def publish(
        self,
        flow_id: str,
        *,
        phone_number_id: str | None = None,
    ) -> WhatsAppFlow:
        """Publish a draft flow to make it available for use."""
        payload: dict[str, Any] = {}
        if phone_number_id is not None:
            payload["phone_number_id"] = phone_number_id
        row = await self._request(
            "POST", f"whatsapp/flows/{flow_id}/publish", json=payload
        )
        return WhatsAppFlow.model_validate(row)

    async def setup_encryption(
        self,
        flow_id: str,
        *,
        phone_number_id: str | None = None,
    ) -> EncryptionResult:
        """Set up flows encryption for the WABA associated with this flow."""
        payload: dict[str, Any] = {}
        if phone_number_id is not None:
            payload["phone_number_id"] = phone_number_id
        row = await self._request(
            "POST", f"whatsapp/flows/{flow_id}/setup_encryption", json=payload
        )
        return EncryptionResult.model_validate(row)

    # ------------------------------------------------------------------ #
    # Versions                                                             #
    # ------------------------------------------------------------------ #

    async def list_versions(
        self,
        flow_id: str,
        *,
        per_page: int = 20,
        page: int = 1,
    ) -> list[FlowVersion]:  # type: ignore[valid-type]
        """List versions for a flow (single page). Use `iter_versions()` for all."""
        params = _filters(per_page=per_page, page=page)
        rows = await self._request(
            "GET", f"whatsapp/flows/{flow_id}/versions", params=params
        )
        return [FlowVersion.model_validate(r) for r in rows]

    async def iter_versions(
        self,
        flow_id: str,
        *,
        per_page: int = 20,
    ) -> AsyncIterator[FlowVersion]:
        """Async iterator over every version of a flow."""
        async for row in self._client.paginate(
            f"whatsapp/flows/{flow_id}/versions", per_page=per_page
        ):
            yield FlowVersion.model_validate(row)

    async def get_version(self, flow_id: str, version_id: str) -> FlowVersion:
        """Fetch a single flow version by id (includes flow_json)."""
        row = await self._request(
            "GET", f"whatsapp/flows/{flow_id}/versions/{version_id}"
        )
        return FlowVersion.model_validate(row)

    async def create_version(
        self,
        flow_id: str,
        *,
        flow_json: dict[str, Any],
        phone_number_id: str | None = None,
    ) -> FlowVersion:
        """Upload new flow JSON to create a new version. Syncs with Meta's API."""
        payload: dict[str, Any] = {"flow_json": flow_json}
        if phone_number_id is not None:
            payload["phone_number_id"] = phone_number_id
        row = await self._request(
            "POST", f"whatsapp/flows/{flow_id}/versions", json=payload
        )
        return FlowVersion.model_validate(row)

    # ------------------------------------------------------------------ #
    # Data endpoint                                                        #
    # ------------------------------------------------------------------ #

    async def get_data_endpoint(self, flow_id: str) -> DataEndpoint:
        """Get the data endpoint function configuration for a flow."""
        row = await self._request("GET", f"whatsapp/flows/{flow_id}/data_endpoint")
        return DataEndpoint.model_validate(row)

    async def upsert_data_endpoint(
        self,
        flow_id: str,
        *,
        code: str,
    ) -> DataEndpoint:
        """Create or update the data endpoint function code (Cloudflare Worker)."""
        row = await self._request(
            "POST",
            f"whatsapp/flows/{flow_id}/data_endpoint",
            json={"code": code},
        )
        return DataEndpoint.model_validate(row)

    async def deploy_data_endpoint(self, flow_id: str) -> DataEndpoint:
        """Deploy the data endpoint function to Cloudflare Workers."""
        row = await self._request(
            "POST", f"whatsapp/flows/{flow_id}/data_endpoint/deploy"
        )
        return DataEndpoint.model_validate(row)

    async def register_data_endpoint_with_meta(
        self, flow_id: str
    ) -> RegisteredDataEndpoint:
        """Register the deployed data endpoint URL with Meta.

        Requires flows encryption to be configured first.
        """
        row = await self._request(
            "POST", f"whatsapp/flows/{flow_id}/data_endpoint/register"
        )
        return RegisteredDataEndpoint.model_validate(row)

    # ------------------------------------------------------------------ #
    # Function observability                                               #
    # ------------------------------------------------------------------ #

    async def get_function_logs(
        self,
        flow_id: str,
        *,
        limit: int = 20,
    ) -> FunctionLogs:
        """Get logs from the data endpoint function (max 50)."""
        params = _filters(limit=limit)
        row = await self._request(
            "GET", f"whatsapp/flows/{flow_id}/function_logs", params=params
        )
        return FunctionLogs.model_validate(row)

    async def get_function_invocations(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        limit: int = 10,
    ) -> FunctionInvocations:
        """Get recent invocations of the data endpoint function (max 20)."""
        params = _filters(status=status, limit=limit)
        row = await self._request(
            "GET", f"whatsapp/flows/{flow_id}/function_invocations", params=params
        )
        return FunctionInvocations.model_validate(row)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
