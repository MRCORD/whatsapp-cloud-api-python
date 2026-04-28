"""
Media resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/media/*
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource


class MediaIngestTarget(BaseModel):
    """Target info returned after a successful media ingest."""

    kind: str | None = None
    media_id: str | None = None


class MediaIngestResource(BaseModel):
    """Resource metadata returned after a successful media ingest."""

    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    source_url: str | None = None


class MediaIngestResult(BaseModel):
    """Response model for the upload-media endpoint."""

    ingest_id: str
    target: MediaIngestTarget | None = None
    resource: MediaIngestResource | None = None


class MediaResource(PlatformBaseResource):
    """Media ingestion for the Kapso Platform API."""

    async def upload(
        self,
        *,
        phone_number_id: str,
        source: str,
        delivery: str = "meta_media",
    ) -> MediaIngestResult:
        """
        Upload media from a public URL for use in WhatsApp messaging.

        Args:
            phone_number_id: WhatsApp phone number ID to associate the media with.
            source: Public URL of the media file to ingest.
            delivery: Delivery method. One of ``meta_media`` (default) or
                ``meta_resumable_asset``.

        Returns:
            MediaIngestResult with ingest_id and target media_id.
        """
        payload: dict[str, Any] = {
            "phone_number_id": phone_number_id,
            "source": source,
            "delivery": delivery,
        }
        row = await self._request(
            "POST",
            "whatsapp/media",
            json={"media_ingest": payload},
        )
        return MediaIngestResult.model_validate(row)
