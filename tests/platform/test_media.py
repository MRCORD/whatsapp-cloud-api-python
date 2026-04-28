"""Tests for the media Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.media import MediaIngestResult

PHONE_NUMBER_ID = "713452918527238"
SOURCE_URL = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Example.png"


def _ingest_result(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "ingest_id": "8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d",
        "target": {
            "kind": "meta_media",
            "media_id": "1234567890123456",
        },
        "resource": {
            "filename": "Example.png",
            "mime_type": "image/png",
            "size_bytes": 2335,
            "sha256": "69da8b7d9c0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
            "source_url": SOURCE_URL,
        },
    }
    base.update(overrides)
    return base


class TestUpload:
    async def test_returns_typed_model(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post("/whatsapp/media").mock(
            return_value=Response(200, json={"data": _ingest_result()})
        )
        result = await platform_client.media.upload(
            phone_number_id=PHONE_NUMBER_ID,
            source=SOURCE_URL,
        )
        assert result.ingest_id == "8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d"
        assert result.target is not None
        assert result.target.kind == "meta_media"
        assert result.target.media_id == "1234567890123456"

    async def test_wraps_payload_in_media_ingest_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/media").mock(
            return_value=Response(200, json={"data": _ingest_result()})
        )
        await platform_client.media.upload(
            phone_number_id=PHONE_NUMBER_ID,
            source=SOURCE_URL,
            delivery="meta_media",
        )
        body = route.calls.last.request.read().decode()
        assert '"media_ingest"' in body
        assert '"phone_number_id"' in body
        assert '"source"' in body
        assert '"delivery":"meta_media"' in body

    async def test_default_delivery_is_meta_media(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/media").mock(
            return_value=Response(200, json={"data": _ingest_result()})
        )
        await platform_client.media.upload(phone_number_id=PHONE_NUMBER_ID, source=SOURCE_URL)
        body = route.calls.last.request.read().decode()
        assert '"delivery":"meta_media"' in body

    async def test_resource_metadata_parsed(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.post("/whatsapp/media").mock(
            return_value=Response(200, json={"data": _ingest_result()})
        )
        result = await platform_client.media.upload(
            phone_number_id=PHONE_NUMBER_ID, source=SOURCE_URL
        )
        assert result.resource is not None
        assert result.resource.filename == "Example.png"
        assert result.resource.mime_type == "image/png"
        assert result.resource.size_bytes == 2335


class TestDocExampleValidates:
    """Regression tests: doc response examples must validate without error."""

    def test_media_upload_doc_example_validates(self) -> None:
        # Source: https://docs.kapso.ai/api/platform/v1/media/upload-media
        # Response 200 meta_media_success — all fields present and non-null.
        example = {
            "ingest_id": "8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d",
            "target": {
                "kind": "meta_media",
                "media_id": "1234567890123456",
            },
            "resource": {
                "filename": "Example.png",
                "mime_type": "image/png",
                "size_bytes": 2335,
                "sha256": "69da8b7d9c0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
                "source_url": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Example.png",
            },
        }
        result = MediaIngestResult.model_validate(example)
        assert result.ingest_id == "8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d"
        assert result.target is not None
        assert result.target.media_id == "1234567890123456"
        assert result.resource is not None
        assert result.resource.size_bytes == 2335
