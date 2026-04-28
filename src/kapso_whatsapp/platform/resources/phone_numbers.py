"""
Phone Numbers resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/phone-numbers/*

  GET    /whatsapp/phone_numbers                                — list
  POST   /customers/{customer_id}/whatsapp/phone_numbers       — connect
  GET    /whatsapp/phone_numbers/{phone_number_id}             — get
  PATCH  /whatsapp/phone_numbers/{phone_number_id}             — update
  DELETE /whatsapp/phone_numbers/{phone_number_id}             — delete
  GET    /whatsapp/phone_numbers/{phone_number_id}/health      — check_health
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class PhoneNumber(BaseModel):
    id: str
    internal_id: str | None = None
    phone_number_id: str | None = None
    name: str | None = None
    business_account_id: str | None = None
    is_coexistence: bool | None = None
    inbound_processing_enabled: bool | None = None
    calls_enabled: bool | None = None
    webhook_verified_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    display_name: str | None = None
    display_phone_number: str | None = None
    display_phone_number_normalized: str | None = None
    verified_name: str | None = None
    quality_rating: str | None = None
    throughput_tier: str | None = None
    whatsapp_business_manager_messaging_limit: str | int | None = None
    customer_id: str | None = None
    code_verification_status: str | None = None
    name_status: str | None = None
    status: str | None = None
    is_official_business_account: bool | None = None
    is_pin_enabled: bool | None = None


class HealthCheckResult(BaseModel):
    passed: bool
    details: dict[str, Any] | None = None
    overall_status: str | None = None


class PhoneHealth(BaseModel):
    status: str
    timestamp: str
    error: str | None = None
    checks: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class PhoneNumbersResource(PlatformBaseResource):
    """Manage WhatsApp phone numbers in the Kapso project."""

    async def list(
        self,
        *,
        phone_number_id: str | None = None,
        business_account_id: str | None = None,
        customer_id: str | None = None,
        messaging_enabled: bool | None = None,
        name_contains: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[PhoneNumber]:
        """List phone numbers (single page). Use `iter()` for full iteration."""
        params = _filters(
            phone_number_id=phone_number_id,
            business_account_id=business_account_id,
            customer_id=customer_id,
            messaging_enabled=messaging_enabled,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/phone_numbers", params=params)
        return [PhoneNumber.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        phone_number_id: str | None = None,
        business_account_id: str | None = None,
        customer_id: str | None = None,
        messaging_enabled: bool | None = None,
        name_contains: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[PhoneNumber]:
        """Async iterator over every phone number matching the filters."""
        params = _filters(
            phone_number_id=phone_number_id,
            business_account_id=business_account_id,
            customer_id=customer_id,
            messaging_enabled=messaging_enabled,
            name_contains=name_contains,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate(
            "whatsapp/phone_numbers", params=params, per_page=per_page
        ):
            yield PhoneNumber.model_validate(row)

    async def connect(
        self,
        customer_id: str,
        *,
        name: str,
        kind: str,
        phone_number_id: str,
        business_account_id: str,
        access_token: str,
        webhook_destination_url: str | None = None,
        webhook_verify_token: str | None = None,
        inbound_processing_enabled: bool | None = None,
        calls_enabled: bool | None = None,
    ) -> PhoneNumber:
        """Connect a WhatsApp number to a customer using Meta credentials."""
        payload: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "phone_number_id": phone_number_id,
            "business_account_id": business_account_id,
            "access_token": access_token,
        }
        if webhook_destination_url is not None:
            payload["webhook_destination_url"] = webhook_destination_url
        if webhook_verify_token is not None:
            payload["webhook_verify_token"] = webhook_verify_token
        if inbound_processing_enabled is not None:
            payload["inbound_processing_enabled"] = inbound_processing_enabled
        if calls_enabled is not None:
            payload["calls_enabled"] = calls_enabled
        row = await self._request(
            "POST",
            f"customers/{customer_id}/whatsapp/phone_numbers",
            json={"whatsapp_phone_number": payload},
        )
        return PhoneNumber.model_validate(row)

    async def get(self, phone_number_id: str) -> PhoneNumber:
        """Fetch a single phone number by Meta phone number ID."""
        row = await self._request(
            "GET", f"whatsapp/phone_numbers/{phone_number_id}"
        )
        return PhoneNumber.model_validate(row)

    async def update(
        self,
        phone_number_id: str,
        *,
        access_token: str | None = None,
        webhook_destination_url: str | None = None,
        webhook_verify_token: str | None = None,
        name: str | None = None,
        inbound_processing_enabled: bool | None = None,
        calls_enabled: bool | None = None,
    ) -> PhoneNumber:
        """Partial update of a phone number (e.g. rotate access token)."""
        payload: dict[str, Any] = {}
        if access_token is not None:
            payload["access_token"] = access_token
        if webhook_destination_url is not None:
            payload["webhook_destination_url"] = webhook_destination_url
        if webhook_verify_token is not None:
            payload["webhook_verify_token"] = webhook_verify_token
        if name is not None:
            payload["name"] = name
        if inbound_processing_enabled is not None:
            payload["inbound_processing_enabled"] = inbound_processing_enabled
        if calls_enabled is not None:
            payload["calls_enabled"] = calls_enabled
        row = await self._request(
            "PATCH",
            f"whatsapp/phone_numbers/{phone_number_id}",
            json={"whatsapp_phone_number": payload},
        )
        return PhoneNumber.model_validate(row)

    async def delete(self, phone_number_id: str) -> None:
        """Delete (disconnect) a phone number. Returns 204 No Content."""
        await self._request("DELETE", f"whatsapp/phone_numbers/{phone_number_id}")

    async def check_health(self, phone_number_id: str) -> PhoneHealth:
        """Live health check via Meta APIs and Kapso services."""
        # Health endpoint returns the full object at top level (no data wrapper).
        raw = await self._client.request_raw(
            "GET", f"whatsapp/phone_numbers/{phone_number_id}/health"
        )
        # The health response is not wrapped in {"data": ...} — it returns the
        # object directly. Use request_raw and parse the envelope ourselves.
        if "data" in raw:
            return PhoneHealth.model_validate(raw["data"])
        return PhoneHealth.model_validate(raw)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
