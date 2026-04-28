"""
Contacts resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/contacts/*
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource


class Contact(BaseModel):
    """A WhatsApp contact as returned by the Kapso Platform API."""

    id: str
    wa_id: str | None = None
    business_scoped_user_id: str | None = None
    parent_business_scoped_user_id: str | None = None
    username: str | None = None
    profile_name: str | None = None
    display_name: str | None = None
    customer_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactsResource(PlatformBaseResource):
    """Manage WhatsApp contacts on your Kapso project."""

    async def list(
        self,
        *,
        customer_id: str | None = None,
        customer_external_id: str | None = None,
        has_customer: bool | None = None,
        profile_name_contains: str | None = None,
        wa_id_contains: str | None = None,
        business_scoped_user_id: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Contact]:
        """List contacts (single page). For full-iteration use `iter()`."""
        params = _filters(
            customer_id=customer_id,
            customer_external_id=customer_external_id,
            has_customer=has_customer,
            profile_name_contains=profile_name_contains,
            wa_id_contains=wa_id_contains,
            business_scoped_user_id=business_scoped_user_id,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/contacts", params=params)
        return [Contact.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        customer_id: str | None = None,
        customer_external_id: str | None = None,
        has_customer: bool | None = None,
        profile_name_contains: str | None = None,
        wa_id_contains: str | None = None,
        business_scoped_user_id: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Contact]:
        """Async iterator over every contact matching the filters."""
        params = _filters(
            customer_id=customer_id,
            customer_external_id=customer_external_id,
            has_customer=has_customer,
            profile_name_contains=profile_name_contains,
            wa_id_contains=wa_id_contains,
            business_scoped_user_id=business_scoped_user_id,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate(
            "whatsapp/contacts", params=params, per_page=per_page
        ):
            yield Contact.model_validate(row)

    async def create(
        self,
        *,
        wa_id: str,
        profile_name: str | None = None,
        display_name: str | None = None,
        customer_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Contact:
        """Create a new WhatsApp contact."""
        payload: dict[str, Any] = {"wa_id": wa_id}
        if profile_name is not None:
            payload["profile_name"] = profile_name
        if display_name is not None:
            payload["display_name"] = display_name
        if customer_id is not None:
            payload["customer_id"] = customer_id
        if metadata is not None:
            payload["metadata"] = metadata
        row = await self._request(
            "POST", "whatsapp/contacts", json={"contact": payload}
        )
        return Contact.model_validate(row)

    async def get(self, identifier: str) -> Contact:
        """Fetch a single contact by UUID or phone number."""
        row = await self._request("GET", f"whatsapp/contacts/{identifier}")
        return Contact.model_validate(row)

    async def erase(self, identifier: str) -> None:
        """Permanently erase a contact and all associated data (async, returns 204)."""
        await self._request("DELETE", f"whatsapp/contacts/{identifier}")

    async def update(
        self,
        identifier: str,
        *,
        wa_id: str | None = None,
        profile_name: str | None = None,
        display_name: str | None = None,
        customer_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Contact:
        """Partial update — only fields you pass are sent."""
        payload: dict[str, Any] = {}
        if wa_id is not None:
            payload["wa_id"] = wa_id
        if profile_name is not None:
            payload["profile_name"] = profile_name
        if display_name is not None:
            payload["display_name"] = display_name
        if customer_id is not None:
            payload["customer_id"] = customer_id
        if metadata is not None:
            payload["metadata"] = metadata
        row = await self._request(
            "PATCH",
            f"whatsapp/contacts/{identifier}",
            json={"contact": payload},
        )
        return Contact.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
