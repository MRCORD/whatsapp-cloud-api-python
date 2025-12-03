"""
Phone Numbers Resource

Handles phone number management including registration,
verification, and business profile settings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class PhoneNumbersResource(BaseResource):
    """
    WhatsApp phone number operations.

    Provides methods for:
    - Requesting and verifying registration codes
    - Registering and deregistering phone numbers
    - Managing phone number settings
    - Updating business profile
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def request_code(
        self,
        *,
        phone_number_id: str,
        code_method: str,
        language: str = "en_US",
    ) -> dict[str, Any]:
        """
        Request a verification code.

        Args:
            phone_number_id: Phone number ID
            code_method: Delivery method (SMS or VOICE)
            language: Language code for the message

        Returns:
            API response
        """
        payload = {
            "code_method": code_method,
            "language": language,
        }

        logger.info(f"Requesting verification code for {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/request_code",
            json=payload,
        )

    async def verify_code(
        self,
        *,
        phone_number_id: str,
        code: str,
    ) -> dict[str, Any]:
        """
        Verify a registration code.

        Args:
            phone_number_id: Phone number ID
            code: Verification code received

        Returns:
            API response
        """
        payload = {"code": code}

        logger.info(f"Verifying code for {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/verify_code",
            json=payload,
        )

    async def register(
        self,
        *,
        phone_number_id: str,
        pin: str,
    ) -> dict[str, Any]:
        """
        Register a phone number.

        Args:
            phone_number_id: Phone number ID
            pin: 6-digit PIN for two-step verification

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "pin": pin,
        }

        logger.info(f"Registering phone number {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/register",
            json=payload,
        )

    async def deregister(
        self,
        *,
        phone_number_id: str,
    ) -> dict[str, Any]:
        """
        Deregister a phone number.

        Args:
            phone_number_id: Phone number ID

        Returns:
            API response
        """
        logger.info(f"Deregistering phone number {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/deregister",
        )

    # =========================================================================
    # Settings
    # =========================================================================

    async def get_settings(
        self,
        *,
        phone_number_id: str,
    ) -> dict[str, Any]:
        """
        Get phone number settings.

        Args:
            phone_number_id: Phone number ID

        Returns:
            Phone number settings
        """
        return await self._request(
            "GET",
            f"{phone_number_id}/whatsapp_business_profile",
        )

    async def update_settings(
        self,
        *,
        phone_number_id: str,
        **settings: Any,
    ) -> dict[str, Any]:
        """
        Update phone number settings.

        Args:
            phone_number_id: Phone number ID
            **settings: Settings to update

        Returns:
            API response
        """
        logger.info(f"Updating settings for {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/settings",
            json=settings,
        )

    # =========================================================================
    # Business Profile
    # =========================================================================

    async def get_business_profile(
        self,
        *,
        phone_number_id: str,
    ) -> dict[str, Any]:
        """
        Get business profile.

        Args:
            phone_number_id: Phone number ID

        Returns:
            Business profile data
        """
        return await self._request(
            "GET",
            f"{phone_number_id}/whatsapp_business_profile",
            params={"fields": "about,address,description,email,profile_picture_url,websites,vertical"},
        )

    async def update_business_profile(
        self,
        *,
        phone_number_id: str,
        about: str | None = None,
        address: str | None = None,
        description: str | None = None,
        email: str | None = None,
        websites: list[str] | None = None,
        vertical: str | None = None,
    ) -> dict[str, Any]:
        """
        Update business profile.

        Args:
            phone_number_id: Phone number ID
            about: Short description (139 chars max)
            address: Business address
            description: Business description (512 chars max)
            email: Business email
            websites: List of website URLs (max 2)
            vertical: Business vertical/industry

        Returns:
            API response
        """
        payload: dict[str, Any] = {"messaging_product": "whatsapp"}

        if about is not None:
            payload["about"] = about
        if address is not None:
            payload["address"] = address
        if description is not None:
            payload["description"] = description
        if email is not None:
            payload["email"] = email
        if websites is not None:
            payload["websites"] = websites
        if vertical is not None:
            payload["vertical"] = vertical

        logger.info(f"Updating business profile for {phone_number_id}")
        return await self._request(
            "POST",
            f"{phone_number_id}/whatsapp_business_profile",
            json=payload,
        )
