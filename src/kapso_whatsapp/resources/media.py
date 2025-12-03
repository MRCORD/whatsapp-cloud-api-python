"""
Media Resource

Handles media upload, download, and management operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from ..types import MediaMetadata, MediaUploadResponse
from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class MediaResource(BaseResource):
    """
    WhatsApp media operations.

    Provides methods for:
    - Uploading media files
    - Getting media metadata and URLs
    - Downloading media content
    - Deleting media

    Example:
        >>> # Upload media
        >>> response = await client.media.upload(
        ...     phone_number_id="123456",
        ...     file=open("photo.jpg", "rb"),
        ...     type="image/jpeg"
        ... )
        >>> print(f"Media ID: {response.id}")
        >>>
        >>> # Download media
        >>> content = await client.media.download(media_id="123...")
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def upload(
        self,
        *,
        phone_number_id: str,
        file: bytes | Any,
        type: str,
        filename: str | None = None,
    ) -> MediaUploadResponse:
        """
        Upload a media file.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            file: File content (bytes or file-like object)
            type: MIME type (e.g., "image/jpeg", "video/mp4")
            filename: Optional filename

        Returns:
            MediaUploadResponse with media ID

        Example:
            >>> with open("photo.jpg", "rb") as f:
            ...     response = await client.media.upload(
            ...         phone_number_id="123456",
            ...         file=f.read(),
            ...         type="image/jpeg",
            ...         filename="photo.jpg"
            ...     )
        """
        files = {
            "file": (filename or "file", file, type),
        }
        data = {
            "messaging_product": "whatsapp",
            "type": type,
        }

        logger.info(f"Uploading media: type={type}")
        response = await self._request(
            "POST",
            f"{phone_number_id}/media",
            data=data,
            files=files,
        )
        return MediaUploadResponse.model_validate(response)

    async def get(
        self,
        *,
        media_id: str,
        phone_number_id: str | None = None,
    ) -> MediaMetadata:
        """
        Get media metadata including download URL.

        Args:
            media_id: Media ID
            phone_number_id: Phone number ID (required for Kapso proxy)

        Returns:
            MediaMetadata with URL and file info

        Example:
            >>> metadata = await client.media.get(media_id="123...")
            >>> print(f"URL: {metadata.url}")
        """
        params: dict[str, Any] = {}
        if phone_number_id:
            params["phone_number_id"] = phone_number_id

        response = await self._request("GET", media_id, params=params or None)
        return MediaMetadata.model_validate(response)

    async def delete(
        self,
        *,
        media_id: str,
        phone_number_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete a media file.

        Args:
            media_id: Media ID to delete
            phone_number_id: Phone number ID (required for Kapso proxy)

        Returns:
            API response confirming deletion
        """
        params: dict[str, Any] = {}
        if phone_number_id:
            params["phone_number_id"] = phone_number_id

        logger.info(f"Deleting media: {media_id}")
        return await self._request("DELETE", media_id, params=params or None)

    async def download(
        self,
        *,
        media_id: str,
        phone_number_id: str | None = None,
        as_: Literal["bytes", "response"] = "bytes",
    ) -> bytes | Any:
        """
        Download media content.

        Automatically handles URL resolution and auth headers.
        Uses raw fetch for public CDN URLs.

        Args:
            media_id: Media ID to download
            phone_number_id: Phone number ID (required for Kapso proxy)
            as_: Return type - "bytes" or "response"

        Returns:
            Media content as bytes or httpx Response

        Example:
            >>> content = await client.media.download(media_id="123...")
            >>> with open("downloaded.jpg", "wb") as f:
            ...     f.write(content)
        """
        # Get media URL first
        metadata = await self.get(media_id=media_id, phone_number_id=phone_number_id)
        url = metadata.url

        # Determine if we need auth headers
        # WhatsApp CDN URLs typically don't need auth
        is_public_cdn = any(
            domain in url
            for domain in ["lookaside.fbsbx.com", "scontent.whatsapp.net"]
        )

        logger.info(f"Downloading media from: {url[:50]}...")

        if is_public_cdn:
            response = await self._client.raw_fetch(url)
        else:
            response = await self._client.fetch(url)

        if as_ == "response":
            return response

        return response.content
