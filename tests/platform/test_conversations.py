"""Tests for the conversations Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient

CONV_ID = "c63ced48-1283-4d55-8c8d-930f525aa0e5"
ASSIGN_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
USER_ID = "f1e2d3c4-b5a6-9870-fedc-ba0987654321"


def _conversation(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": CONV_ID,
        "phone_number": "14155550123",
        "status": "active",
        "last_active_at": "2025-07-16T09:45:00Z",
        "created_at": "2025-06-01T12:00:00Z",
        "updated_at": "2025-07-16T09:45:00Z",
        "metadata": {},
        "phone_number_id": "1234567890",
        "kapso": {
            "contact_name": "Alicia",
            "messages_count": 42,
            "last_message_id": "wamid.HBgMMTIzNDU2",
            "last_message_type": "text",
            "last_message_timestamp": "2025-07-16T09:40:00Z",
            "last_message_text": "Thanks!",
            "last_inbound_at": "2025-07-16T09:35:10Z",
            "last_outbound_at": "2025-07-16T09:40:00Z",
        },
    }
    base.update(overrides)
    return base


def _assignment(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": ASSIGN_ID,
        "user_id": USER_ID,
        "created_by_user_id": USER_ID,
        "notes": "Handling customer inquiry about pricing",
        "active": True,
        "created_at": "2026-01-19T10:30:00Z",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/conversations").mock(
            return_value=Response(
                200,
                json={
                    "data": [_conversation(), _conversation(id="conv-2", status="ended")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        convs = await platform_client.conversations.list()
        assert len(convs) == 2
        assert convs[0].status == "active"
        assert convs[1].status == "ended"

    async def test_passes_filters_as_query_params(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/conversations").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.conversations.list(status="active", per_page=10, page=3)
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "active"
        assert params["per_page"] == "10"
        assert params["page"] == "3"

    async def test_omits_none_filters(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.get("/whatsapp/conversations").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.conversations.list()
        params = dict(route.calls.last.request.url.params)
        assert "status" not in params
        assert "assigned_user_id" not in params

    async def test_kapso_meta_parsed(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/conversations").mock(
            return_value=Response(
                200,
                json={
                    "data": [_conversation()],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 1},
                },
            )
        )
        convs = await platform_client.conversations.list()
        assert convs[0].kapso is not None
        assert convs[0].kapso.contact_name == "Alicia"
        assert convs[0].kapso.messages_count == 42


class TestIter:
    async def test_iterates_across_pages(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get("/whatsapp/conversations", params={"page": "1", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_conversation(id="c1"), _conversation(id="c2")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get("/whatsapp/conversations", params={"page": "2", "per_page": "2"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_conversation(id="c3")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        ids = [c.id async for c in platform_client.conversations.iter(per_page=2)]
        assert ids == ["c1", "c2", "c3"]


class TestGet:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/conversations/{CONV_ID}").mock(
            return_value=Response(200, json={"data": _conversation()})
        )
        result = await platform_client.conversations.get(CONV_ID)
        assert result.id == CONV_ID
        assert result.phone_number == "14155550123"


class TestUpdateStatus:
    async def test_wraps_payload_in_whatsapp_conversation_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch(f"/whatsapp/conversations/{CONV_ID}").mock(
            return_value=Response(200, json={"data": _conversation(status="ended")})
        )
        result = await platform_client.conversations.update_status(CONV_ID, status="ended")
        assert result.status == "ended"
        body = route.calls.last.request.read().decode()
        assert '"whatsapp_conversation"' in body
        assert '"status":"ended"' in body


class TestListAssignments:
    async def test_returns_assignment_list(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(f"/whatsapp/conversations/{CONV_ID}/assignments").mock(
            return_value=Response(
                200,
                json={
                    "data": [_assignment(), _assignment(id="b2", active=False)],
                    "meta": {"page": 1, "per_page": 25, "total_pages": 1, "total_count": 2},
                },
            )
        )
        assignments = await platform_client.conversations.list_assignments(CONV_ID)
        assert len(assignments) == 2
        assert assignments[0].active is True
        assert assignments[1].active is False


class TestCreateAssignment:
    async def test_wraps_payload_in_assignment_key(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/conversations/{CONV_ID}/assignments").mock(
            return_value=Response(201, json={"data": _assignment()})
        )
        result = await platform_client.conversations.create_assignment(
            CONV_ID, user_id=USER_ID, notes="Customer needs help"
        )
        assert result.user_id == USER_ID
        assert result.active is True
        body = route.calls.last.request.read().decode()
        assert '"assignment"' in body
        assert '"user_id"' in body

    async def test_omits_notes_when_not_provided(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.post(f"/whatsapp/conversations/{CONV_ID}/assignments").mock(
            return_value=Response(201, json={"data": _assignment(notes=None)})
        )
        await platform_client.conversations.create_assignment(CONV_ID, user_id=USER_ID)
        body = route.calls.last.request.read().decode()
        assert "notes" not in body


class TestGetAssignment:
    async def test_unwraps_data(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        mock_platform_api.get(
            f"/whatsapp/conversations/{CONV_ID}/assignments/{ASSIGN_ID}"
        ).mock(return_value=Response(200, json={"data": _assignment()}))
        result = await platform_client.conversations.get_assignment(CONV_ID, ASSIGN_ID)
        assert result.id == ASSIGN_ID
        assert result.notes == "Handling customer inquiry about pricing"


class TestUpdateAssignment:
    async def test_partial_update_sends_only_provided_fields(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch(
            f"/whatsapp/conversations/{CONV_ID}/assignments/{ASSIGN_ID}"
        ).mock(return_value=Response(200, json={"data": _assignment(notes="Resolved")}))
        result = await platform_client.conversations.update_assignment(
            CONV_ID, ASSIGN_ID, notes="Resolved"
        )
        assert result.notes == "Resolved"
        body = route.calls.last.request.read().decode()
        assert '"assignment"' in body
        assert '"notes":"Resolved"' in body
        assert "user_id" not in body

    async def test_deactivate_assignment(
        self, platform_client: KapsoPlatformClient, mock_platform_api: respx.MockRouter
    ) -> None:
        route = mock_platform_api.patch(
            f"/whatsapp/conversations/{CONV_ID}/assignments/{ASSIGN_ID}"
        ).mock(return_value=Response(200, json={"data": _assignment(active=False)}))
        result = await platform_client.conversations.update_assignment(
            CONV_ID, ASSIGN_ID, active=False
        )
        assert result.active is False
        body = route.calls.last.request.read().decode()
        assert '"active":false' in body
