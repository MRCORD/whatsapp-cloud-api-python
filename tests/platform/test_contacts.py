"""Tests for the contacts Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient

CONTACT_ID = "123e4567-e89b-12d3-a456-426614174000"


def _contact(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": CONTACT_ID,
        "wa_id": "15551234567",
        "business_scoped_user_id": "US.13491208655302741918",
        "parent_business_scoped_user_id": "US.ENT.506847293015824",
        "username": "@testusername",
        "profile_name": "John Doe",
        "display_name": "John (VIP)",
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metadata": {"segment": "vip"},
        "created_at": "2025-03-26T15:05:00.000000Z",
        "updated_at": "2025-03-26T15:05:00.000000Z",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/contacts").mock(
            return_value=Response(
                200,
                json={
                    "data": [_contact(), _contact(id="2", profile_name="Jane Smith")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        contacts = await platform_client.contacts.list()
        assert len(contacts) == 2
        assert contacts[0].profile_name == "John Doe"
        assert contacts[1].profile_name == "Jane Smith"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/contacts").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.contacts.list(profile_name_contains="John", per_page=50, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["profile_name_contains"] == "John"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/contacts").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.contacts.list()
        params = dict(route.calls.last.request.url.params)
        assert "customer_id" not in params
        assert "profile_name_contains" not in params


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/contacts", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_contact(id="1"), _contact(id="2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/whatsapp/contacts", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_contact(id="3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        ids = [c.id async for c in platform_client.contacts.iter(per_page=2)]
        assert ids == ["1", "2", "3"]


class TestCreate:
    async def test_wraps_payload_in_contact_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/contacts").mock(
            return_value=Response(201, json={"data": _contact()})
        )
        result = await platform_client.contacts.create(
            wa_id="+15551234567",
            profile_name="John Doe",
            display_name="John (VIP)",
        )
        assert result.profile_name == "John Doe"
        body = route.calls.last.request.read().decode()
        assert '"contact"' in body
        assert '"wa_id"' in body

    async def test_omits_optional_fields_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post("/whatsapp/contacts").mock(
            return_value=Response(201, json={"data": _contact(display_name=None, customer_id=None)})
        )
        await platform_client.contacts.create(wa_id="+15551234567")
        body = route.calls.last.request.read().decode()
        assert "display_name" not in body
        assert "customer_id" not in body


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/contacts/{CONTACT_ID}").mock(
            return_value=Response(200, json={"data": _contact()})
        )
        result = await platform_client.contacts.get(CONTACT_ID)
        assert result.id == CONTACT_ID
        assert result.wa_id == "15551234567"

    async def test_accepts_phone_number_as_identifier(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/contacts/+15551234567").mock(
            return_value=Response(200, json={"data": _contact()})
        )
        result = await platform_client.contacts.get("+15551234567")
        assert result.wa_id == "15551234567"


class TestErase:
    async def test_returns_none_on_204(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.delete(f"/whatsapp/contacts/{CONTACT_ID}").mock(
            return_value=Response(204)
        )
        result = await platform_client.contacts.erase(CONTACT_ID)
        assert result is None


class TestUpdate:
    async def test_wraps_payload_in_contact_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch(f"/whatsapp/contacts/{CONTACT_ID}").mock(
            return_value=Response(200, json={"data": _contact(display_name="Johnny")})
        )
        result = await platform_client.contacts.update(CONTACT_ID, display_name="Johnny")
        assert result.display_name == "Johnny"
        body = route.calls.last.request.read().decode()
        assert '"contact"' in body
        assert '"display_name":"Johnny"' in body

    async def test_partial_update_omits_unset_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch(f"/whatsapp/contacts/{CONTACT_ID}").mock(
            return_value=Response(200, json={"data": _contact()})
        )
        await platform_client.contacts.update(CONTACT_ID, profile_name="Johnny Doe")
        body = route.calls.last.request.read().decode()
        assert '"profile_name":"Johnny Doe"' in body
        assert "display_name" not in body
        assert "customer_id" not in body


class TestDocExampleValidates:
    """Regression guard: doc example from docs.kapso.ai/api/platform/v1/contacts/get-contact
    must remain parseable by Contact without modification."""

    def test_contact_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.contacts import Contact

        example = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "wa_id": "15551234567",
            "business_scoped_user_id": "US.13491208655302741918",
            "parent_business_scoped_user_id": "US.ENT.506847293015824",
            "username": "@testusername",
            "profile_name": "John Doe",
            "display_name": "John (VIP)",
            "customer_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "metadata": {},
            "created_at": "2023-11-07T05:31:56Z",
            "updated_at": "2023-11-07T05:31:56Z",
        }
        Contact.model_validate(example)  # raises if model gets stricter than docs
