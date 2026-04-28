"""
Setup Links resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/setup-links/*

All three endpoints are scoped under a customer:
  GET    /customers/{customer_id}/setup_links
  POST   /customers/{customer_id}/setup_links
  PATCH  /customers/{customer_id}/setup_links/{setup_link_id}
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ProvisionedPhoneNumber(BaseModel):
    id: str
    phone_number: str | None = None
    status: str | None = None
    country_iso: str | None = None
    country_dial_code: str | None = None
    area_code: str | None = None
    display_number: str | None = None


class ThemeConfig(BaseModel):
    primary_color: str | None = None
    primary_foreground_color: str | None = None
    background_color: str | None = None
    text_color: str | None = None
    muted_text_color: str | None = None
    card_color: str | None = None
    muted_color: str | None = None
    border_color: str | None = None
    secondary_color: str | None = None
    secondary_foreground_color: str | None = None
    destructive_color: str | None = None
    destructive_foreground_color: str | None = None


class SetupLink(BaseModel):
    id: str
    status: str
    created_at: str
    url: str | None = None
    expires_at: str | None = None
    success_redirect_url: str | None = None
    failure_redirect_url: str | None = None
    allowed_connection_types: list[str] | None = None
    theme_config: ThemeConfig | None = None
    provision_phone_number: bool | None = None
    phone_number_area_code: str | None = None
    phone_number_country_isos: list[str] | None = None
    language: str | None = None
    whatsapp_setup_status: str | None = None
    whatsapp_setup_error: str | None = None
    provisioned_phone_number: ProvisionedPhoneNumber | None = None


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class SetupLinksResource(PlatformBaseResource):
    """Manage WhatsApp onboarding setup links for a customer."""

    def _path(self, customer_id: str, setup_link_id: str | None = None) -> str:
        base = f"customers/{customer_id}/setup_links"
        if setup_link_id is not None:
            return f"{base}/{setup_link_id}"
        return base

    async def list(
        self,
        customer_id: str,
        *,
        status: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[SetupLink]:
        """List setup links for a customer (single page). Use `iter()` for full iteration."""
        params = _filters(
            status=status,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", self._path(customer_id), params=params)
        return [SetupLink.model_validate(r) for r in rows]

    async def iter(
        self,
        customer_id: str,
        *,
        status: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[SetupLink]:
        """Async iterator over every setup link for a customer."""
        params = _filters(
            status=status,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate(
            self._path(customer_id), params=params, per_page=per_page
        ):
            yield SetupLink.model_validate(row)

    async def create(
        self,
        customer_id: str,
        *,
        success_redirect_url: str | None = None,
        failure_redirect_url: str | None = None,
        allowed_connection_types: list[str] | None = None,  # type: ignore[valid-type]
        theme_config: dict[str, Any] | None = None,
        provision_phone_number: bool | None = None,
        phone_number_area_code: str | None = None,
        phone_number_country_isos: list[str] | None = None,  # type: ignore[valid-type]
        language: str | None = None,
    ) -> SetupLink:
        """Create a new setup link for a customer."""
        payload: dict[str, Any] = {}
        if success_redirect_url is not None:
            payload["success_redirect_url"] = success_redirect_url
        if failure_redirect_url is not None:
            payload["failure_redirect_url"] = failure_redirect_url
        if allowed_connection_types is not None:
            payload["allowed_connection_types"] = allowed_connection_types
        if theme_config is not None:
            payload["theme_config"] = theme_config
        if provision_phone_number is not None:
            payload["provision_phone_number"] = provision_phone_number
        if phone_number_area_code is not None:
            payload["phone_number_area_code"] = phone_number_area_code
        if phone_number_country_isos is not None:
            payload["phone_number_country_isos"] = phone_number_country_isos
        if language is not None:
            payload["language"] = language
        row = await self._request(
            "POST",
            self._path(customer_id),
            json={"setup_link": payload},
        )
        return SetupLink.model_validate(row)

    async def update(
        self,
        customer_id: str,
        setup_link_id: str,
        *,
        status: str | None = None,
        success_redirect_url: str | None = None,
        failure_redirect_url: str | None = None,
    ) -> SetupLink:
        """Partial update of a setup link (e.g. revoke it)."""
        payload: dict[str, Any] = {}
        if status is not None:
            payload["status"] = status
        if success_redirect_url is not None:
            payload["success_redirect_url"] = success_redirect_url
        if failure_redirect_url is not None:
            payload["failure_redirect_url"] = failure_redirect_url
        row = await self._request(
            "PATCH",
            self._path(customer_id, setup_link_id),
            json={"setup_link": payload},
        )
        return SetupLink.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
