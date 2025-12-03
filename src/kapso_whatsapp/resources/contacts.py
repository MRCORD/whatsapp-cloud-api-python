"""
Contacts Resource (Kapso Proxy Only)

Handles contact management operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class ContactsResource(BaseResource):
    """
    WhatsApp contacts operations (Kapso proxy only).

    Provides methods for:
    - Listing contacts
    - Getting contact details
    - Updating contact metadata
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def list(
        self,
        *,
        phone_number_id: str,
        customer_id: str | None = None,
        limit: int = 50,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        List contacts.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            customer_id: Filter by customer ID
            limit: Maximum contacts to return
            after: Pagination cursor

        Returns:
            Paginated list of contacts
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {
            "phone_number_id": phone_number_id,
            "limit": limit,
        }

        if customer_id:
            params["customer_id"] = customer_id
        if after:
            params["after"] = after

        return await self._request("GET", "contacts", params=params)

    async def get(
        self,
        *,
        phone_number_id: str,
        wa_id: str,
    ) -> dict[str, Any]:
        """
        Get contact details.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            wa_id: WhatsApp ID of the contact

        Returns:
            Contact details
        """
        self._require_kapso_proxy()

        return await self._request(
            "GET",
            f"contacts/{wa_id}",
            params={"phone_number_id": phone_number_id},
        )

    async def update(
        self,
        *,
        phone_number_id: str,
        wa_id: str,
        name: str | None = None,
        customer_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update contact.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            wa_id: WhatsApp ID of the contact
            name: Contact name
            customer_id: Customer ID for linking
            metadata: Custom metadata

        Returns:
            Updated contact
        """
        self._require_kapso_proxy()

        payload: dict[str, Any] = {"phone_number_id": phone_number_id}

        if name is not None:
            payload["name"] = name
        if customer_id is not None:
            payload["customer_id"] = customer_id
        if metadata is not None:
            payload["metadata"] = metadata

        logger.info(f"Updating contact {wa_id}")
        return await self._request(
            "PATCH",
            f"contacts/{wa_id}",
            json=payload,
        )
