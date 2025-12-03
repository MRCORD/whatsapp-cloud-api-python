"""
Templates Resource

Handles template management operations including listing,
creating, and deleting message templates.

Ported from flowers-backend with TypeScript SDK alignment.
"""

from __future__ import annotations

import builtins
import logging
from typing import TYPE_CHECKING, Any

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class TemplatesResource(BaseResource):
    """
    WhatsApp templates operations.

    Provides methods for managing message templates:
    - List templates
    - Create templates
    - Delete templates
    - Get template details

    Note: Templates must be approved by WhatsApp before use.
    Template creation and management can also be done through
    the Kapso dashboard or Meta Business Manager.

    Example:
        >>> # List templates
        >>> templates = await client.templates.list(business_account_id="123...")
        >>> for t in templates["data"]:
        ...     print(f"{t['name']}: {t['status']}")
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def list(
        self,
        *,
        business_account_id: str,
        name: str | None = None,
        status: str | None = None,
        category: str | None = None,
        language: str | None = None,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        List message templates for business account.

        Args:
            business_account_id: WhatsApp Business Account ID
            name: Filter by template name
            status: Filter by status (APPROVED, PENDING, REJECTED)
            category: Filter by category (AUTHENTICATION, MARKETING, UTILITY)
            language: Filter by language code (e.g., 'en_US', 'es', 'pt_BR')
            limit: Maximum results per page (default 20, max 100)
            before: Cursor for previous page (Base64 encoded)
            after: Cursor for next page (Base64 encoded)

        Returns:
            Paginated list of templates

        Example:
            >>> # List all templates
            >>> templates = await client.templates.list(
            ...     business_account_id="123456789"
            ... )
            >>> for template in templates['data']:
            ...     print(template['name'], template['status'])
            >>> # Filter by status and category
            >>> templates = await client.templates.list(
            ...     business_account_id="123456789",
            ...     status="APPROVED",
            ...     category="MARKETING"
            ... )
        """
        params: dict[str, Any] = {"limit": limit}

        if name:
            params["name"] = name
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        logger.info(f"Listing templates for business account {business_account_id}")
        return await self._request(
            "GET",
            f"{business_account_id}/message_templates",
            params=params,
        )

    async def get(self, *, template_id: str) -> dict[str, Any]:
        """
        Get details of a specific template.

        Args:
            template_id: Template ID

        Returns:
            Template details

        Example:
            >>> template = await client.templates.get(template_id="123456789")
            >>> print(template['name'], template['status'], template['category'])
        """
        logger.info(f"Getting template details for {template_id}")
        return await self._request("GET", template_id)

    async def create(
        self,
        *,
        business_account_id: str,
        name: str,
        language: str,
        category: str,
        components: builtins.list[dict[str, Any]],
        parameter_format: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new message template.

        Args:
            business_account_id: WhatsApp Business Account ID
            name: Template name (lowercase, underscore separated)
            language: Language code (e.g., 'en_US', 'es', 'pt_BR')
            category: Template category (UTILITY, MARKETING, AUTHENTICATION)
            components: Template components (HEADER, BODY, FOOTER, BUTTONS)
            parameter_format: Parameter format (POSITIONAL or NAMED)

        Returns:
            Template creation result

        Note:
            Templates require WhatsApp approval before use.
            Approval typically takes 1-2 hours but can take up to 24 hours.

        Example:
            >>> result = await client.templates.create(
            ...     business_account_id="123456789",
            ...     name="order_confirmation",
            ...     category="UTILITY",
            ...     language="es",
            ...     components=[
            ...         {
            ...             "type": "BODY",
            ...             "text": "Hola {{1}}, tu pedido {{2}} ha sido confirmado!",
            ...             "example": {"body_text": [["Jessica", "ORDER123"]]}
            ...         }
            ...     ]
            ... )
        """
        payload: dict[str, Any] = {
            "name": name,
            "category": category,
            "language": language,
            "components": components,
        }

        if parameter_format:
            payload["parameter_format"] = parameter_format

        logger.info(f"Creating template '{name}' for business account {business_account_id}")
        return await self._request(
            "POST",
            f"{business_account_id}/message_templates",
            json=payload,
        )

    async def delete(
        self,
        *,
        business_account_id: str,
        name: str | None = None,
        hsm_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete a message template.

        Specify either `name` or `hsm_id` to identify the template to delete.

        Args:
            business_account_id: WhatsApp Business Account ID
            name: Template name to delete (use this OR hsm_id)
            hsm_id: Template ID to delete (use this OR name)

        Returns:
            Deletion result with success status

        Note:
            Deleted templates cannot be recovered.

        Raises:
            ValueError: If neither name nor hsm_id is provided, or if both are provided

        Example:
            >>> # Delete by name
            >>> await client.templates.delete(
            ...     business_account_id="123456789",
            ...     name="order_confirmation"
            ... )
            >>> # Delete by ID
            >>> await client.templates.delete(
            ...     business_account_id="123456789",
            ...     hsm_id="template-id-here"
            ... )
        """
        if not name and not hsm_id:
            raise ValueError("Must specify either 'name' or 'hsm_id'")
        if name and hsm_id:
            raise ValueError("Specify only one of 'name' or 'hsm_id', not both")

        params: dict[str, Any] = {}
        if name:
            params["name"] = name
        if hsm_id:
            params["hsm_id"] = hsm_id

        identifier = name or hsm_id
        logger.info(f"Deleting template '{identifier}' from business account {business_account_id}")
        return await self._request(
            "DELETE",
            f"{business_account_id}/message_templates",
            params=params,
        )
