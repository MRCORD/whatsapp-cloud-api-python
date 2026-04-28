"""
Conversations resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/conversations/*
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource


class ConversationKapsoMeta(BaseModel):
    """Kapso-specific extensions on a WhatsApp conversation."""

    contact_name: str | None = None
    messages_count: int | None = None
    last_message_id: str | None = None
    last_message_type: str | None = None
    last_message_timestamp: str | None = None
    last_message_text: str | None = None
    last_inbound_at: str | None = None
    last_outbound_at: str | None = None


class Conversation(BaseModel):
    """A WhatsApp conversation as returned by the Kapso Platform API."""

    id: str
    phone_number: str | None = None
    status: str | None = None
    last_active_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] | None = None
    phone_number_id: str | None = None
    kapso: ConversationKapsoMeta | None = None


class ConversationAssignment(BaseModel):
    """A conversation assignment record."""

    id: str
    user_id: str | None = None
    created_by_user_id: str | None = None
    notes: str | None = None
    active: bool | None = None
    created_at: str | None = None


class ConversationsResource(PlatformBaseResource):
    """Manage WhatsApp conversations on your Kapso project."""

    # -------------------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------------------

    async def list(
        self,
        *,
        phone_number_id: str | None = None,
        phone_number: str | None = None,
        status: str | None = None,
        assigned_user_id: str | None = None,
        unassigned: bool | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        last_active_after: str | None = None,
        last_active_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Conversation]:
        """List conversations (single page). For full-iteration use `iter()`."""
        params = _filters(
            phone_number_id=phone_number_id,
            phone_number=phone_number,
            status=status,
            assigned_user_id=assigned_user_id,
            unassigned=unassigned,
            created_after=created_after,
            created_before=created_before,
            last_active_after=last_active_after,
            last_active_before=last_active_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "whatsapp/conversations", params=params)
        return [Conversation.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        phone_number_id: str | None = None,
        phone_number: str | None = None,
        status: str | None = None,
        assigned_user_id: str | None = None,
        unassigned: bool | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        last_active_after: str | None = None,
        last_active_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Conversation]:
        """Async iterator over every conversation matching the filters."""
        params = _filters(
            phone_number_id=phone_number_id,
            phone_number=phone_number,
            status=status,
            assigned_user_id=assigned_user_id,
            unassigned=unassigned,
            created_after=created_after,
            created_before=created_before,
            last_active_after=last_active_after,
            last_active_before=last_active_before,
        )
        async for row in self._client.paginate(
            "whatsapp/conversations", params=params, per_page=per_page
        ):
            yield Conversation.model_validate(row)

    async def get(self, conversation_id: str) -> Conversation:
        """Fetch a single conversation by id."""
        row = await self._request("GET", f"whatsapp/conversations/{conversation_id}")
        return Conversation.model_validate(row)

    async def update_status(
        self,
        conversation_id: str,
        *,
        status: str,
    ) -> Conversation:
        """Update the status of a conversation (e.g. 'ended' or 'active')."""
        row = await self._request(
            "PATCH",
            f"whatsapp/conversations/{conversation_id}",
            json={"whatsapp_conversation": {"status": status}},
        )
        return Conversation.model_validate(row)

    # -------------------------------------------------------------------------
    # Assignments (sub-resource of conversations)
    # -------------------------------------------------------------------------

    async def list_assignments(
        self,
        conversation_id: str,
        *,
        per_page: int = 25,
        page: int = 1,
    ) -> list[ConversationAssignment]:  # type: ignore[valid-type]
        """List all assignments for a conversation, most recent first."""
        params = _filters(per_page=per_page, page=page)
        rows = await self._request(
            "GET",
            f"whatsapp/conversations/{conversation_id}/assignments",
            params=params,
        )
        return [ConversationAssignment.model_validate(r) for r in rows]

    async def create_assignment(
        self,
        conversation_id: str,
        *,
        user_id: str,
        notes: str | None = None,
    ) -> ConversationAssignment:
        """Assign a conversation to a team member."""
        payload: dict[str, Any] = {"user_id": user_id}
        if notes is not None:
            payload["notes"] = notes
        row = await self._request(
            "POST",
            f"whatsapp/conversations/{conversation_id}/assignments",
            json={"assignment": payload},
        )
        return ConversationAssignment.model_validate(row)

    async def get_assignment(
        self,
        conversation_id: str,
        assignment_id: str,
    ) -> ConversationAssignment:
        """Retrieve a specific assignment by ID."""
        row = await self._request(
            "GET",
            f"whatsapp/conversations/{conversation_id}/assignments/{assignment_id}",
        )
        return ConversationAssignment.model_validate(row)

    async def update_assignment(
        self,
        conversation_id: str,
        assignment_id: str,
        *,
        user_id: str | None = None,
        notes: str | None = None,
        active: bool | None = None,
    ) -> ConversationAssignment:
        """Update an assignment's notes, reassign to another user, or deactivate."""
        payload: dict[str, Any] = {}
        if user_id is not None:
            payload["user_id"] = user_id
        if notes is not None:
            payload["notes"] = notes
        if active is not None:
            payload["active"] = active
        row = await self._request(
            "PATCH",
            f"whatsapp/conversations/{conversation_id}/assignments/{assignment_id}",
            json={"assignment": payload},
        )
        return ConversationAssignment.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
