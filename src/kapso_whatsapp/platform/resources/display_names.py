"""
Display Names resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/display-names/*

All endpoints are scoped under a phone number:
  GET  /whatsapp/phone_numbers/{phone_number_id}/display_name_requests
  POST /whatsapp/phone_numbers/{phone_number_id}/display_name_requests
  GET  /whatsapp/phone_numbers/{phone_number_id}/display_name_requests/{request_id}

Note: the list endpoint uses a non-standard meta key (current_page instead of page).
The paginator reads meta.page, so the iter() implementation reads raw envelopes to
handle both spellings gracefully.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DisplayNameRequest(BaseModel):
    id: str
    phone_number_id: str
    requested_display_name: str
    previous_display_name: str | None = None
    status: str
    submitted_at: str | None = None
    reviewed_at: str | None = None
    applied_at: str | None = None
    meta_error_code: int | None = None
    meta_error_subcode: int | None = None
    meta_error_type: str | None = None
    meta_error_message: str | None = None


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class DisplayNamesResource(PlatformBaseResource):
    """Manage WhatsApp display name change requests for a phone number."""

    def _base_path(self, phone_number_id: str) -> str:
        return f"whatsapp/phone_numbers/{phone_number_id}/display_name_requests"

    async def list(
        self,
        phone_number_id: str,
        *,
        per_page: int = 20,
        page: int = 1,
    ) -> list[DisplayNameRequest]:
        """List display name requests for a phone number (single page).
        Use `iter()` for full pagination."""
        params = _filters(per_page=per_page, page=page)
        rows = await self._request(
            "GET", self._base_path(phone_number_id), params=params
        )
        return [DisplayNameRequest.model_validate(r) for r in rows]

    async def iter(
        self,
        phone_number_id: str,
        *,
        per_page: int = 20,
    ) -> AsyncIterator[DisplayNameRequest]:
        """Async iterator over every display name request for a phone number."""
        async for row in self._client.paginate(
            self._base_path(phone_number_id), per_page=per_page
        ):
            yield DisplayNameRequest.model_validate(row)

    async def submit(
        self,
        phone_number_id: str,
        *,
        new_display_name: str,
    ) -> DisplayNameRequest:
        """Submit a display name change request."""
        row = await self._request(
            "POST",
            self._base_path(phone_number_id),
            json={"display_name_request": {"new_display_name": new_display_name}},
        )
        return DisplayNameRequest.model_validate(row)

    async def retrieve(
        self,
        phone_number_id: str,
        request_id: str,
    ) -> DisplayNameRequest:
        """Retrieve a single display name request by ID."""
        row = await self._request(
            "GET",
            f"{self._base_path(phone_number_id)}/{request_id}",
        )
        return DisplayNameRequest.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
