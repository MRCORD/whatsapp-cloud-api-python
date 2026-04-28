"""
Broadcasts resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/broadcasts/*

Workflow: create broadcast -> add recipients -> send (or schedule).

Public methods:
  * list(...)            — fetch one page of broadcasts (returns list[Broadcast])
  * iter(...)            — async generator across all pages (yields Broadcast)
  * get(broadcast_id)    — single broadcast by id
  * create(...)          — create a broadcast in draft status
  * list_recipients(...) — one page of recipients for a broadcast
  * iter_recipients(...) — async generator across all recipient pages
  * add_recipients(...)  — add up to 1000 recipients to a draft broadcast
  * send(broadcast_id)   — start sending immediately (async on the API side)
  * schedule(broadcast_id, scheduled_at=...) — schedule for a future time
  * cancel(broadcast_id) — cancel a scheduled broadcast (returns to draft)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource

# =============================================================================
# Models
# =============================================================================


class WhatsAppTemplateComponent(BaseModel):
    """A single component within a WhatsApp template."""

    model_config = ConfigDict(extra="allow")

    type: str
    text: str | None = None
    example: dict[str, Any] | None = None


class WhatsAppTemplate(BaseModel):
    """Embedded WhatsApp template on a broadcast."""

    model_config = ConfigDict(extra="allow")

    id: str
    meta_template_id: str | None = None
    name: str
    language_code: str | None = None
    category: str | None = None
    status: str | None = None
    components: list[WhatsAppTemplateComponent] = []


class Broadcast(BaseModel):
    """A WhatsApp broadcast campaign."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    status: str
    phone_number_id: str | None = None
    whatsapp_template: WhatsAppTemplate | None = None
    started_at: str | None = None
    completed_at: str | None = None
    scheduled_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    responded_count: int = 0
    pending_count: int = 0
    response_rate: float = 0.0


class RecipientTemplateParameter(BaseModel):
    """A single template parameter for a recipient."""

    model_config = ConfigDict(extra="allow")

    type: str
    parameter_name: str | None = None
    text: str | None = None


class RecipientTemplateComponent(BaseModel):
    """A template component attached to a recipient."""

    model_config = ConfigDict(extra="allow")

    type: str
    parameters: list[RecipientTemplateParameter] = []


class BroadcastRecipient(BaseModel):
    """A single recipient within a broadcast, with delivery status."""

    model_config = ConfigDict(extra="allow")

    id: str
    phone_number: str
    status: str
    sent_at: str | None = None
    delivered_at: str | None = None
    read_at: str | None = None
    responded_at: str | None = None
    failed_at: str | None = None
    error_message: str | None = None
    error_details: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    template_components: list[RecipientTemplateComponent] = []


class AddRecipientsResult(BaseModel):
    """Result returned after adding recipients to a broadcast."""

    model_config = ConfigDict(extra="allow")

    added: int
    duplicates: int = 0
    errors: list[str] = []


class BroadcastActionResult(BaseModel):
    """Minimal result returned by send / schedule / cancel actions."""

    model_config = ConfigDict(extra="allow")

    id: str
    status: str
    scheduled_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


# =============================================================================
# Resource
# =============================================================================


class BroadcastsResource(PlatformBaseResource):
    """Manage WhatsApp broadcast campaigns on your Kapso project."""

    # -------------------------------------------------------------------------
    # Broadcasts
    # -------------------------------------------------------------------------

    async def list(
        self,
        *,
        phone_number_id: str | None = None,
        status: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Broadcast]:
        """List broadcasts (single page). For full iteration use `iter()`."""
        params = _filters(
            phone_number_id=phone_number_id,
            status=status,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/broadcasts", params=params)
        return [Broadcast.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        phone_number_id: str | None = None,
        status: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Broadcast]:
        """Async iterator over every broadcast matching the filters."""
        params = _filters(
            phone_number_id=phone_number_id,
            status=status,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate(
            "whatsapp/broadcasts", params=params, per_page=per_page
        ):
            yield Broadcast.model_validate(row)

    async def get(self, broadcast_id: str) -> Broadcast:
        """Fetch a single broadcast by id."""
        row = await self._request("GET", f"whatsapp/broadcasts/{broadcast_id}")
        return Broadcast.model_validate(row)

    async def create(
        self,
        *,
        name: str,
        phone_number_id: str,
        whatsapp_template_id: str,
    ) -> Broadcast:
        """Create a new broadcast in draft status.

        Workflow: create -> add_recipients -> send (or schedule).
        """
        payload: dict[str, Any] = {
            "name": name,
            "phone_number_id": phone_number_id,
            "whatsapp_template_id": whatsapp_template_id,
        }
        row = await self._request(
            "POST",
            "whatsapp/broadcasts",
            json={"whatsapp_broadcast": payload},
        )
        return Broadcast.model_validate(row)

    # -------------------------------------------------------------------------
    # Recipients sub-resource
    # -------------------------------------------------------------------------

    async def list_recipients(
        self,
        broadcast_id: str,
        *,
        per_page: int = 20,
        page: int = 1,
    ) -> list[BroadcastRecipient]:  # type: ignore[valid-type]
        """List recipients for a broadcast (single page).

        For full iteration use `iter_recipients()`.
        """
        params = _filters(per_page=per_page, page=page)
        rows = await self._request(
            "GET",
            f"whatsapp/broadcasts/{broadcast_id}/recipients",
            params=params,
        )
        return [BroadcastRecipient.model_validate(r) for r in rows]

    async def iter_recipients(
        self,
        broadcast_id: str,
        *,
        per_page: int = 20,
    ) -> AsyncIterator[BroadcastRecipient]:
        """Async iterator over every recipient for a broadcast."""
        async for row in self._client.paginate(
            f"whatsapp/broadcasts/{broadcast_id}/recipients",
            per_page=per_page,
        ):
            yield BroadcastRecipient.model_validate(row)

    async def add_recipients(
        self,
        broadcast_id: str,
        *,
        recipients: list[dict[str, Any]],  # type: ignore[valid-type]
    ) -> AddRecipientsResult:
        """Add up to 1000 recipients to a draft broadcast.

        Each recipient dict must have at minimum a ``phone_number`` key and
        optionally a ``components`` list following Meta's template component
        syntax (body, header, button components).

        Duplicates are skipped automatically by the API.
        """
        row = await self._request(
            "POST",
            f"whatsapp/broadcasts/{broadcast_id}/recipients",
            json={"whatsapp_broadcast": {"recipients": recipients}},
        )
        return AddRecipientsResult.model_validate(row)

    # -------------------------------------------------------------------------
    # Action endpoints
    # -------------------------------------------------------------------------

    async def send(self, broadcast_id: str) -> BroadcastActionResult:
        """Start sending a draft broadcast immediately.

        The operation is asynchronous on the API side. Poll
        ``get(broadcast_id)`` to track progress.
        """
        row = await self._request(
            "POST",
            f"whatsapp/broadcasts/{broadcast_id}/send",
        )
        return BroadcastActionResult.model_validate(row)

    async def schedule(
        self,
        broadcast_id: str,
        *,
        scheduled_at: str,
    ) -> BroadcastActionResult:
        """Schedule a draft broadcast to send at a future ISO-8601 time.

        Args:
            broadcast_id: UUID of the broadcast to schedule.
            scheduled_at: ISO-8601 timestamp with timezone, must be in the
                future (e.g. ``"2025-10-12T17:00:00Z"``).
        """
        row = await self._request(
            "POST",
            f"whatsapp/broadcasts/{broadcast_id}/schedule",
            json={"scheduled_at": scheduled_at},
        )
        return BroadcastActionResult.model_validate(row)

    async def cancel(self, broadcast_id: str) -> BroadcastActionResult:
        """Cancel a scheduled broadcast and return it to draft status.

        Only broadcasts in ``scheduled`` status can be cancelled.
        """
        row = await self._request(
            "POST",
            f"whatsapp/broadcasts/{broadcast_id}/cancel",
        )
        return BroadcastActionResult.model_validate(row)


# =============================================================================
# Helpers
# =============================================================================


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
