"""
Conversations Resource (Kapso Proxy Only)

Handles conversation management operations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class ConversationsResource(BaseResource):
    """
    WhatsApp conversations operations (Kapso proxy only).

    Provides methods for:
    - Listing conversations
    - Getting conversation details
    - Updating conversation status
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def list(
        self,
        *,
        phone_number_id: str,
        status: Literal["active", "ended"] | None = None,
        last_active_since: datetime | str | None = None,
        last_active_until: datetime | str | None = None,
        phone_number: str | None = None,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """
        List conversations.

        Conversations are ordered by last activity (most recent first).
        Supports filtering by status, activity time range, and phone number.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            status: Filter by conversation status ('active' or 'ended')
            last_active_since: Filter conversations active on or after this time (ISO 8601)
            last_active_until: Filter conversations active on or before this time (ISO 8601)
            phone_number: Filter by contact phone number
            limit: Maximum results per page (default 20, max 100)
            before: Cursor for previous page (Base64 encoded)
            after: Cursor for next page (Base64 encoded)
            fields: Filter response fields. Use 'kapso()' to include Kapso extensions.

        Returns:
            Paginated list of conversations with Kapso metadata

        Example:
            >>> # List active conversations
            >>> await client.conversations.list(
            ...     phone_number_id="123456",
            ...     status="active"
            ... )
            >>> # List with time filter and Kapso extensions
            >>> await client.conversations.list(
            ...     phone_number_id="123456",
            ...     last_active_since="2024-01-01T00:00:00Z",
            ...     fields="kapso()"
            ... )
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {"limit": limit}

        if status:
            params["status"] = status
        if last_active_since:
            if isinstance(last_active_since, datetime):
                params["last_active_since"] = last_active_since.isoformat()
            else:
                params["last_active_since"] = last_active_since
        if last_active_until:
            if isinstance(last_active_until, datetime):
                params["last_active_until"] = last_active_until.isoformat()
            else:
                params["last_active_until"] = last_active_until
        if phone_number:
            params["phone_number"] = phone_number
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if fields:
            params["fields"] = fields

        return await self._request("GET", f"{phone_number_id}/conversations", params=params)

    async def get(
        self,
        *,
        phone_number_id: str,
        conversation_id: str,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """
        Get conversation details.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            conversation_id: Conversation ID (UUID)
            fields: Filter response fields. Use 'kapso()' to include Kapso extensions.

        Returns:
            Conversation details with optional Kapso metadata

        Example:
            >>> # Get basic conversation details
            >>> await client.conversations.get(
            ...     phone_number_id="123456",
            ...     conversation_id="conv-uuid-here"
            ... )
            >>> # Get with Kapso extensions
            >>> await client.conversations.get(
            ...     phone_number_id="123456",
            ...     conversation_id="conv-uuid-here",
            ...     fields="kapso()"
            ... )
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields

        return await self._request(
            "GET",
            f"{phone_number_id}/conversations/{conversation_id}",
            params=params if params else None,
        )

    async def update_status(
        self,
        *,
        conversation_id: str,
        status: Literal["active", "ended"],
    ) -> dict[str, Any]:
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status

        Returns:
            Updated conversation
        """
        self._require_kapso_proxy()

        logger.info(f"Updating conversation {conversation_id} status to {status}")
        return await self._request(
            "PATCH",
            f"conversations/{conversation_id}",
            json={"status": status},
        )
