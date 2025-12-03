"""
Calls Resource (Kapso Proxy Only)

Handles call operations and call logs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class CallsResource(BaseResource):
    """
    WhatsApp calls operations (Kapso proxy only).

    Provides methods for:
    - Listing call logs
    - Getting call details
    - Initiating calls
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def list(
        self,
        *,
        phone_number_id: str,
        direction: Literal["INBOUND", "OUTBOUND"] | None = None,
        limit: int = 50,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        List call logs.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            direction: Filter by direction
            limit: Maximum calls to return
            after: Pagination cursor

        Returns:
            Paginated list of calls
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {
            "phone_number_id": phone_number_id,
            "limit": limit,
        }

        if direction:
            params["direction"] = direction
        if after:
            params["after"] = after

        return await self._request("GET", "calls", params=params)

    async def get(
        self,
        *,
        phone_number_id: str,
        call_id: str,
    ) -> dict[str, Any]:
        """
        Get call details.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            call_id: Call ID

        Returns:
            Call details
        """
        self._require_kapso_proxy()

        return await self._request(
            "GET",
            f"calls/{call_id}",
            params={"phone_number_id": phone_number_id},
        )

    async def request_permission(
        self,
        *,
        phone_number_id: str,
        to: str,
        call_type: Literal["AUDIO", "VIDEO"] = "AUDIO",
    ) -> dict[str, Any]:
        """
        Request call permission from a user.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            call_type: Type of call

        Returns:
            Permission request result
        """
        self._require_kapso_proxy()

        payload = {
            "phone_number_id": phone_number_id,
            "to": to,
            "call_type": call_type,
        }

        logger.info(f"Requesting call permission for {to}")
        return await self._request("POST", "calls/permission", json=payload)
