"""Tests for the messages Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient


def _message(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "wamid.HBgMMTIzNDU2Nzg5MBUCABIYGTA5RTlCQkI2NTI3",
        "timestamp": "1705395000",
        "type": "text",
        "from": "14155550123",
        "text": {"body": "Hello, I need help with my order"},
        "kapso": {
            "direction": "inbound",
            "status": "delivered",
            "processing_status": "processed",
            "origin": "cloud_api",
            "phone_number": "14155550123",
            "phone_number_id": "123456789012345",
            "has_media": False,
            "whatsapp_conversation_id": "c63ced48-1283-4d55-8c8d-930f525aa0e5",
            "contact_name": "Alicia",
            "content": "Hello, I need help with my order",
        },
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/messages").mock(
            return_value=Response(
                200,
                json={
                    "data": [_message(), _message(id="wamid.2", type="image")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        messages = await platform_client.messages.list()
        assert len(messages) == 2
        assert messages[0].id == "wamid.HBgMMTIzNDU2Nzg5MBUCABIYGTA5RTlCQkI2NTI3"
        assert messages[1].type == "image"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/messages").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 50, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.messages.list(direction="inbound", per_page=50, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["direction"] == "inbound"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/messages").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.messages.list()
        params = dict(route.calls.last.request.url.params)
        assert "direction" not in params
        assert "status" not in params

    async def test_kapso_meta_parsed(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/messages").mock(
            return_value=Response(
                200,
                json={
                    "data": [_message()],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 1},
                },
            )
        )
        messages = await platform_client.messages.list()
        assert messages[0].kapso is not None
        assert messages[0].kapso.direction == "inbound"
        assert messages[0].kapso.has_media is False


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/messages", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_message(id="wamid.1"), _message(id="wamid.2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/whatsapp/messages", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_message(id="wamid.3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        ids = [m.id async for m in platform_client.messages.iter(per_page=2)]
        assert ids == ["wamid.1", "wamid.2", "wamid.3"]


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/messages/wamid.abc").mock(
            return_value=Response(200, json={"data": _message(id="wamid.abc")})
        )
        result = await platform_client.messages.get("wamid.abc")
        assert result.id == "wamid.abc"

    async def test_from_field_remapped(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/messages/wamid.xyz").mock(
            return_value=Response(200, json={"data": _message(id="wamid.xyz")})
        )
        result = await platform_client.messages.get("wamid.xyz")
        assert result.from_ == "14155550123"


class TestDocExampleValidates:
    """Regression guard: doc example from docs.kapso.ai/api/platform/v1/messages/get-message
    must remain parseable by Message without modification."""

    def test_message_doc_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.messages import Message

        example = {
            "id": "wamid.HBgMMTIzNDU2Nzg5MBUCABIYGTA5RTlCQkI2NTI3",
            "timestamp": "1705395000",
            "type": "text",
            "from": "14155550123",
            "text": {
                "body": "Hello, I need help with my order",
            },
            "kapso": {
                "direction": "inbound",
                "status": "read",
                "processing_status": "processed",
                "origin": "cloud_api",
                "phone_number": "14155550123",
                "phone_number_id": "123456789012345",
                "has_media": False,
                "whatsapp_conversation_id": "c63ced48-1283-4d55-8c8d-930f525aa0e5",
                "contact_name": "Alicia",
                "content": "Hello, I need help with my order",
                "statuses": [
                    {
                        "id": "wamid.HBgMMTIzNDU2Nzg5MBUCABIYGTA5RTlCQkI2NTI3",
                        "status": "delivered",
                        "timestamp": "1705395005",
                        "recipient_id": "14155550123",
                    },
                    {
                        "id": "wamid.HBgMMTIzNDU2Nzg5MBUCABIYGTA5RTlCQkI2NTI3",
                        "status": "read",
                        "timestamp": "1705395300",
                        "recipient_id": "14155550123",
                    },
                ],
            },
        }
        Message.model_validate(example)  # raises if model gets stricter than docs


# =============================================================================
# BSUID compatibility (rolling out 2026)
# =============================================================================


class TestBsuidShapes:
    """Verify the Message model accepts both Kapso-shape and Meta-shape
    BSUID identity fields (per docs/platform/whatsapp-data)."""

    def test_kapso_shape_bsuid_fields_validate(self) -> None:
        from kapso_whatsapp.platform.resources.messages import Message

        msg = Message.model_validate({
            "id": "msg-1",
            "type": "text",
            "from": "16315551181",
            "business_scoped_user_id": "US.13491208655302741918",
            "parent_business_scoped_user_id": "US.ENT.506847293015824",
            "username": "@u",
        })
        assert msg.business_scoped_user_id == "US.13491208655302741918"
        assert msg.parent_business_scoped_user_id == "US.ENT.506847293015824"
        assert msg.username == "@u"

    def test_meta_shape_user_id_fields_validate(self) -> None:
        """Meta-shape alternate: from_user_id/to_user_id instead of
        business_scoped_user_id. Doc lists them as alternates on message
        payloads."""
        from kapso_whatsapp.platform.resources.messages import Message

        msg = Message.model_validate({
            "id": "msg-2",
            "type": "text",
            "from_user_id": "US.111",
            "from_parent_user_id": "US.ENT.222",
            "to_user_id": "US.333",
            "to_parent_user_id": "US.ENT.444",
            "username": "@m",
        })
        assert msg.from_user_id == "US.111"
        assert msg.from_parent_user_id == "US.ENT.222"
        assert msg.to_user_id == "US.333"
        assert msg.to_parent_user_id == "US.ENT.444"

    def test_no_phone_no_wa_id_validates(self) -> None:
        """A message with neither `from` nor any BSUID field still validates
        (id is the only required field)."""
        from kapso_whatsapp.platform.resources.messages import Message

        msg = Message.model_validate({"id": "msg-3"})
        assert msg.from_ is None
        assert msg.business_scoped_user_id is None
