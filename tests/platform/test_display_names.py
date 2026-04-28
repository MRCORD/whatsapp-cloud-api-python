"""Tests for the display_names Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient

PHONE_NUMBER_ID = "1234567890"
REQUEST_ID = "2b0f4a1e-7a58-4a15-b0c9-0d7f1a2b3c4d"


def _display_name_request(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": REQUEST_ID,
        "phone_number_id": PHONE_NUMBER_ID,
        "requested_display_name": "Acme Support",
        "previous_display_name": "+1 555-123-4567",
        "status": "pending_review",
        "submitted_at": "2025-07-14T15:00:00Z",
        "reviewed_at": None,
        "applied_at": None,
        "meta_error_code": None,
        "meta_error_subcode": None,
        "meta_error_type": None,
        "meta_error_message": None,
    }
    base.update(overrides)
    return base


_BASE = f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}/display_name_requests"


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(_BASE).mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        _display_name_request(),
                        _display_name_request(id="other", status="applied"),
                    ],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        result = await platform_client.display_names.list(PHONE_NUMBER_ID)
        assert len(result) == 2
        assert result[0].status == "pending_review"
        assert result[1].status == "applied"

    async def test_passes_pagination_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get(_BASE).mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 2, "per_page": 5, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.display_names.list(PHONE_NUMBER_ID, per_page=5, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["per_page"] == "5"
        assert params["page"] == "2"


class TestIter:
    async def test_iterates_across_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(_BASE, params={"page": "1", "per_page": "1"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_display_name_request(id="r1", requested_display_name="Name A")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get(_BASE, params={"page": "2", "per_page": "1"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_display_name_request(id="r2", requested_display_name="Name B")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        names = [
            r.requested_display_name
            async for r in platform_client.display_names.iter(PHONE_NUMBER_ID, per_page=1)
        ]
        assert names == ["Name A", "Name B"]


class TestSubmit:
    async def test_wraps_payload_in_display_name_request_key(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(_BASE).mock(
            return_value=Response(201, json={"data": _display_name_request()})
        )
        result = await platform_client.display_names.submit(
            PHONE_NUMBER_ID, new_display_name="Acme Support"
        )
        assert result.requested_display_name == "Acme Support"
        assert result.status == "pending_review"
        body = route.calls.last.request.read().decode()
        assert '"display_name_request"' in body
        assert '"new_display_name":"Acme Support"' in body

    async def test_returns_display_name_request_model(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.post(_BASE).mock(
            return_value=Response(
                201,
                json={
                    "data": _display_name_request(
                        requested_display_name="TechCorp",
                        status="pending_review",
                    )
                },
            )
        )
        result = await platform_client.display_names.submit(
            PHONE_NUMBER_ID, new_display_name="TechCorp"
        )
        assert result.id == REQUEST_ID
        assert result.phone_number_id == PHONE_NUMBER_ID


class TestRetrieve:
    async def test_fetches_single_request_by_id(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(f"{_BASE}/{REQUEST_ID}").mock(
            return_value=Response(
                200,
                json={
                    "data": _display_name_request(
                        status="approved",
                        reviewed_at="2025-07-15T12:34:00Z",
                        applied_at="2025-07-16T09:00:00Z",
                    )
                },
            )
        )
        result = await platform_client.display_names.retrieve(
            PHONE_NUMBER_ID, REQUEST_ID
        )
        assert result.id == REQUEST_ID
        assert result.status == "approved"
        assert result.reviewed_at == "2025-07-15T12:34:00Z"

    async def test_declined_request_has_error_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(f"{_BASE}/{REQUEST_ID}").mock(
            return_value=Response(
                200,
                json={
                    "data": _display_name_request(
                        status="declined",
                        meta_error_code=100,
                        meta_error_type="OAuthException",
                        meta_error_message="Display name does not match",
                    )
                },
            )
        )
        result = await platform_client.display_names.retrieve(
            PHONE_NUMBER_ID, REQUEST_ID
        )
        assert result.status == "declined"
        assert result.meta_error_code == 100
        assert result.meta_error_message == "Display name does not match"
