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
        wa_id: str | None = None,
        customer_id: str | None = None,
        has_customer: bool | None = None,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """
        List contacts.

        Contacts are returned in a paginated format with cursor-based navigation.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            wa_id: Filter by WhatsApp ID (phone number)
            customer_id: Filter by associated customer ID
            has_customer: Filter by customer association (true/false)
            limit: Maximum results per page (default 20, max 100)
            before: Cursor for previous page (Base64 encoded)
            after: Cursor for next page (Base64 encoded)
            fields: Filter response fields. Use 'kapso()' to include Kapso extensions.

        Returns:
            Paginated list of contacts

        Example:
            >>> # List all contacts
            >>> await client.contacts.list(phone_number_id="123456")
            >>> # Filter by WhatsApp ID
            >>> await client.contacts.list(
            ...     phone_number_id="123456",
            ...     wa_id="15551234567"
            ... )
            >>> # Filter contacts with customer association
            >>> await client.contacts.list(
            ...     phone_number_id="123456",
            ...     has_customer=True
            ... )
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {"limit": limit}

        if wa_id:
            params["wa_id"] = wa_id
        if customer_id:
            params["customer_id"] = customer_id
        if has_customer is not None:
            params["has_customer"] = has_customer
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if fields:
            params["fields"] = fields

        return await self._request("GET", f"{phone_number_id}/contacts", params=params)

    async def get(
        self,
        *,
        phone_number_id: str,
        wa_id: str,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """
        Get contact details.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            wa_id: WhatsApp ID of the contact
            fields: Filter response fields. Use 'kapso()' to include Kapso extensions.

        Returns:
            Contact details with optional Kapso metadata

        Example:
            >>> # Get basic contact details
            >>> await client.contacts.get(
            ...     phone_number_id="123456",
            ...     wa_id="15551234567"
            ... )
            >>> # Get with Kapso extensions
            >>> await client.contacts.get(
            ...     phone_number_id="123456",
            ...     wa_id="15551234567",
            ...     fields="kapso()"
            ... )
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields

        return await self._request(
            "GET",
            f"{phone_number_id}/contacts/{wa_id}",
            params=params if params else None,
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
