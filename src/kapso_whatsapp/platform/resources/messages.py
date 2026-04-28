"""
Messages resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/messages/*
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource


class MessageKapsoMeta(BaseModel):
    """Kapso-specific extensions on a WhatsApp message."""

    model_config = ConfigDict(extra="allow")

    direction: str | None = None
    status: str | None = None
    processing_status: str | None = None
    origin: str | None = None
    phone_number: str | None = None
    phone_number_id: str | None = None
    has_media: bool | None = None
    whatsapp_conversation_id: str | None = None
    contact_name: str | None = None
    content: str | None = None
    statuses: list[dict[str, Any]] | None = None


class Message(BaseModel):
    """A WhatsApp message as returned by the Kapso Platform API.

    Identity fields cover both the Kapso shape (``business_scoped_user_id`` etc.)
    and the Meta shape (``from_user_id``, ``to_user_id`` etc.) per
    https://docs.kapso.ai/docs/platform/whatsapp-data — depending on the
    payload variant returned, one or the other will be populated.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    timestamp: str | None = None
    type: str | None = None
    from_: str | None = None
    kapso: MessageKapsoMeta | None = None
    text: dict[str, Any] | None = None

    # Kapso-shape BSUID identity (additive)
    business_scoped_user_id: str | None = None
    parent_business_scoped_user_id: str | None = None
    username: str | None = None

    # Meta-shape identity (alternate to the Kapso-shape fields above)
    from_user_id: str | None = None
    from_parent_user_id: str | None = None
    to_user_id: str | None = None
    to_parent_user_id: str | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> Message:
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = dict(obj)
            obj["from_"] = obj.pop("from")
        return super().model_validate(obj, **kwargs)


class MessagesResource(PlatformBaseResource):
    """Read WhatsApp messages from your Kapso project."""

    async def list(
        self,
        *,
        phone_number_id: str | None = None,
        conversation_id: str | None = None,
        phone_number: str | None = None,
        business_scoped_user_id: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        message_type: str | None = None,
        has_media: bool | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Message]:
        """List messages (single page). For full-iteration use `iter()`."""
        params = _filters(
            phone_number_id=phone_number_id,
            conversation_id=conversation_id,
            phone_number=phone_number,
            business_scoped_user_id=business_scoped_user_id,
            direction=direction,
            status=status,
            message_type=message_type,
            has_media=has_media,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/messages", params=params)
        return [Message.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        phone_number_id: str | None = None,
        conversation_id: str | None = None,
        phone_number: str | None = None,
        business_scoped_user_id: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        message_type: str | None = None,
        has_media: bool | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Message]:
        """Async iterator over every message matching the filters."""
        params = _filters(
            phone_number_id=phone_number_id,
            conversation_id=conversation_id,
            phone_number=phone_number,
            business_scoped_user_id=business_scoped_user_id,
            direction=direction,
            status=status,
            message_type=message_type,
            has_media=has_media,
        )
        async for row in self._client.paginate(
            "whatsapp/messages", params=params, per_page=per_page
        ):
            yield Message.model_validate(row)

    async def get(self, message_id: str) -> Message:
        """Fetch a single message by its WhatsApp message ID (WAMID)."""
        row = await self._request("GET", f"whatsapp/messages/{message_id}")
        return Message.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
