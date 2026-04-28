"""Tests for the phone_numbers Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient

PHONE_NUMBER_ID = "1234567890"
CUSTOMER_ID = "3f2e1d0c-9b8a-7f6e-5d4c-3b2a1f0e9d8c"


def _phone_number(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": PHONE_NUMBER_ID,
        "internal_id": "4a5b6c7d-8e9f-0a1b-2c3d-4e5f6a7b8c9d",
        "phone_number_id": PHONE_NUMBER_ID,
        "name": "Support Line",
        "business_account_id": "98765432109",
        "is_coexistence": False,
        "inbound_processing_enabled": True,
        "calls_enabled": False,
        "webhook_verified_at": "2025-01-14T15:10:00Z",
        "created_at": "2025-01-14T15:00:00Z",
        "updated_at": "2025-01-14T15:10:00Z",
        "display_name": "Support Line",
        "display_phone_number": "+1 555-123-4567",
        "display_phone_number_normalized": "15551234567",
        "verified_name": "Acme Corp",
        "quality_rating": "GREEN",
        "throughput_tier": "TIER_10K",
        "whatsapp_business_manager_messaging_limit": "10000",
        "customer_id": CUSTOMER_ID,
        "code_verification_status": "COMPLETED",
        "name_status": "APPROVED",
        "status": "CONNECTED",
        "is_official_business_account": False,
        "is_pin_enabled": True,
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/whatsapp/phone_numbers").mock(
            return_value=Response(
                200,
                json={
                    "data": [_phone_number(), _phone_number(id="other", name="Line 2")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        result = await platform_client.phone_numbers.list()
        assert len(result) == 2
        assert result[0].name == "Support Line"
        assert result[1].name == "Line 2"

    async def test_passes_filters_as_query_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/whatsapp/phone_numbers").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 5, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.phone_numbers.list(
            customer_id=CUSTOMER_ID, name_contains="Support", per_page=5, page=2
        )
        params = dict(route.calls.last.request.url.params)
        assert params["customer_id"] == CUSTOMER_ID
        assert params["name_contains"] == "Support"
        assert params["per_page"] == "5"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/whatsapp/phone_numbers").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.phone_numbers.list()
        params = dict(route.calls.last.request.url.params)
        assert "customer_id" not in params
        assert "name_contains" not in params


class TestIter:
    async def test_iterates_across_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(
            "/whatsapp/phone_numbers", params={"page": "1", "per_page": "1"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_phone_number(id="1", name="a")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get(
            "/whatsapp/phone_numbers", params={"page": "2", "per_page": "1"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_phone_number(id="2", name="b")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        names = [pn.name async for pn in platform_client.phone_numbers.iter(per_page=1)]
        assert names == ["a", "b"]


class TestConnect:
    async def test_wraps_payload_in_whatsapp_phone_number_key(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            f"/customers/{CUSTOMER_ID}/whatsapp/phone_numbers"
        ).mock(
            return_value=Response(201, json={"data": _phone_number()})
        )
        result = await platform_client.phone_numbers.connect(
            CUSTOMER_ID,
            name="Support Line",
            kind="production",
            phone_number_id=PHONE_NUMBER_ID,
            business_account_id="98765432109",
            access_token="EAABsbCS...token",
            inbound_processing_enabled=True,
        )
        assert result.name == "Support Line"
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_phone_number"' in body
        assert '"name":"Support Line"' in body
        assert '"access_token"' in body

    async def test_optional_fields_omitted_when_not_provided(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            f"/customers/{CUSTOMER_ID}/whatsapp/phone_numbers"
        ).mock(
            return_value=Response(201, json={"data": _phone_number()})
        )
        await platform_client.phone_numbers.connect(
            CUSTOMER_ID,
            name="Line",
            kind="production",
            phone_number_id="123",
            business_account_id="456",
            access_token="tok",
        )
        body = route.calls.last.request.read().decode()
        assert "webhook_destination_url" not in body
        assert "webhook_verify_token" not in body


class TestGet:
    async def test_unwraps_data(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}").mock(
            return_value=Response(200, json={"data": _phone_number()})
        )
        result = await platform_client.phone_numbers.get(PHONE_NUMBER_ID)
        assert result.id == PHONE_NUMBER_ID
        assert result.verified_name == "Acme Corp"


class TestUpdate:
    async def test_wraps_in_whatsapp_phone_number_key(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch(
            f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}"
        ).mock(
            return_value=Response(200, json={"data": _phone_number()})
        )
        await platform_client.phone_numbers.update(
            PHONE_NUMBER_ID, access_token="new-token"
        )
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_phone_number"' in body
        assert '"access_token":"new-token"' in body

    async def test_partial_update_only_sends_provided_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch(
            f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}"
        ).mock(
            return_value=Response(200, json={"data": _phone_number()})
        )
        await platform_client.phone_numbers.update(
            PHONE_NUMBER_ID, access_token="tok"
        )
        body = route.calls.last.request.read().decode()
        assert "webhook_destination_url" not in body
        assert "name" not in body


class TestDelete:
    async def test_returns_none_on_204(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.delete(f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}").mock(
            return_value=Response(204)
        )
        result = await platform_client.phone_numbers.delete(PHONE_NUMBER_ID)
        assert result is None


class TestCheckHealth:
    async def test_returns_phone_health_model(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        health_payload = {
            "status": "healthy",
            "timestamp": "2025-01-20T14:25:30Z",
            "checks": {
                "phone_number_access": {"passed": True, "details": {}},
                "messaging_health": {"passed": True, "overall_status": "AVAILABLE", "details": {}},
            },
        }
        mock_platform_api.get(
            f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}/health"
        ).mock(return_value=Response(200, json=health_payload))
        result = await platform_client.phone_numbers.check_health(PHONE_NUMBER_ID)
        assert result.status == "healthy"
        assert result.timestamp == "2025-01-20T14:25:30Z"
        assert result.checks is not None

    async def test_unhealthy_status_is_parsed(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(
            f"/whatsapp/phone_numbers/{PHONE_NUMBER_ID}/health"
        ).mock(
            return_value=Response(
                200,
                json={
                    "status": "unhealthy",
                    "timestamp": "2025-01-20T14:25:30Z",
                    "error": "Token expired",
                    "checks": {},
                },
            )
        )
        result = await platform_client.phone_numbers.check_health(PHONE_NUMBER_ID)
        assert result.status == "unhealthy"
        assert result.error == "Token expired"


class TestDocExampleValidates:
    """Regression guard: doc example from docs.kapso.ai/api/platform/v1/phone-numbers/get-phone-number
    must remain parseable by PhoneNumber without modification."""

    def test_phone_number_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.phone_numbers import PhoneNumber

        example = {
            "id": "<string>",
            "internal_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "phone_number_id": "<string>",
            "name": "<string>",
            "created_at": "2023-11-07T05:31:56Z",
            "updated_at": "2023-11-07T05:31:56Z",
            "business_account_id": "<string>",
            "is_coexistence": True,
            "inbound_processing_enabled": True,
            "calls_enabled": True,
            "webhook_verified_at": "2023-11-07T05:31:56Z",
            "customer_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "display_name": "<string>",
            "display_phone_number": "<string>",
            "display_phone_number_normalized": "<string>",
            "verified_name": "<string>",
            "quality_rating": "<string>",
            "code_verification_status": "<string>",
            "name_status": "<string>",
            "status": "<string>",
            "throughput_tier": "<string>",
            "whatsapp_business_manager_messaging_limit": 123,
            "is_official_business_account": True,
            "is_pin_enabled": True,
        }
        PhoneNumber.model_validate(example)  # raises if model gets stricter than docs
