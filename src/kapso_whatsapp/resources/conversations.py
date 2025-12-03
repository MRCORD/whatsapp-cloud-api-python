"""
Conversations Resource (Kapso Proxy Only)

Handles conversation management operations.
"""

from __future__ import annotations

import logging
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
        status: Literal["active", "ended", "expired"] | None = None,
        limit: int = 50,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        List conversations.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            status: Filter by status
            limit: Maximum conversations to return
            after: Pagination cursor

        Returns:
            Paginated list of conversations
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {
            "phone_number_id": phone_number_id,
            "limit": limit,
        }

        if status:
            params["status"] = status
        if after:
            params["after"] = after

        return await self._request("GET", "conversations", params=params)

    async def get(
        self,
        *,
        conversation_id: str,
    ) -> dict[str, Any]:
        """
        Get conversation details.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation details
        """
        self._require_kapso_proxy()

        return await self._request("GET", f"conversations/{conversation_id}")

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
