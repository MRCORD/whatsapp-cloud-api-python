"""Tests for the broadcasts Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.broadcasts import (
    AddRecipientsResult,
    Broadcast,
    BroadcastActionResult,
    BroadcastRecipient,
)

# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def _broadcast(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c",
        "name": "Weekend Sale 2025",
        "status": "draft",
        "phone_number_id": "1234567890",
        "whatsapp_template": {
            "id": "784203120908608",
            "meta_template_id": "784203120908608",
            "name": "weekend_sale_2025",
            "language_code": "en_US",
            "category": "MARKETING",
            "status": "approved",
            "components": [],
        },
        "started_at": None,
        "completed_at": None,
        "created_at": "2025-07-14T15:00:00Z",
        "updated_at": "2025-07-14T15:00:00Z",
        "total_recipients": 0,
        "sent_count": 0,
        "failed_count": 0,
        "delivered_count": 0,
        "read_count": 0,
        "responded_count": 0,
        "pending_count": 0,
        "response_rate": 0.0,
    }
    base.update(overrides)
    return base


def _recipient(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "8c9d0e1f-2a3b-4c5d-6e7f-8a9b0c1d2e3f",
        "phone_number": "14155550123",
        "status": "sent",
        "sent_at": "2025-07-15T10:05:23Z",
        "delivered_at": "2025-07-15T10:05:30Z",
        "read_at": None,
        "responded_at": None,
        "created_at": "2025-07-15T10:00:00Z",
        "updated_at": "2025-07-15T10:05:30Z",
        "template_components": [],
    }
    base.update(overrides)
    return base


def _action_result(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c",
        "status": "sending",
        "scheduled_at": None,
        "started_at": "2025-10-12T17:03:21Z",
        "completed_at": None,
    }
    base.update(overrides)
    return base


def _paginated(items: list[dict], *, page: int = 1, total_pages: int = 1) -> dict:
    return {
        "data": items,
        "meta": {
            "page": page,
            "per_page": 20,
            "total_pages": total_pages,
            "total_count": len(items),
        },
    }


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/whatsapp/broadcasts").mock(
            return_value=Response(
                200,
                json=_paginated(
                    [_broadcast(), _broadcast(id="2", name="Product Launch")]
                ),
            )
        )
        results = await platform_client.broadcasts.list()
        assert len(results) == 2
        assert all(isinstance(b, Broadcast) for b in results)
        assert results[0].name == "Weekend Sale 2025"
        assert results[1].name == "Product Launch"

    async def test_passes_filters_as_query_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/whatsapp/broadcasts").mock(
            return_value=Response(200, json=_paginated([]))
        )
        await platform_client.broadcasts.list(
            phone_number_id="123",
            status="completed",
            per_page=50,
            page=2,
        )
        params = dict(route.calls.last.request.url.params)
        assert params["phone_number_id"] == "123"
        assert params["status"] == "completed"
        assert params["per_page"] == "50"
        assert params["page"] == "2"

    async def test_omits_none_filters(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/whatsapp/broadcasts").mock(
            return_value=Response(200, json=_paginated([]))
        )
        await platform_client.broadcasts.list()
        params = dict(route.calls.last.request.url.params)
        assert "phone_number_id" not in params
        assert "status" not in params

    async def test_model_fields_populated(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/whatsapp/broadcasts").mock(
            return_value=Response(
                200,
                json=_paginated([_broadcast(status="completed", total_recipients=1000)]),
            )
        )
        results = await platform_client.broadcasts.list()
        b = results[0]
        assert b.status == "completed"
        assert b.total_recipients == 1000
        assert b.whatsapp_template is not None
        assert b.whatsapp_template.name == "weekend_sale_2025"


# ---------------------------------------------------------------------------
# iter
# ---------------------------------------------------------------------------


class TestIter:
    async def test_iterates_across_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(
            "/whatsapp/broadcasts", params={"page": "1", "per_page": "2"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_broadcast(id="1", name="a"), _broadcast(id="2", name="b")],
                    "meta": {"page": 1, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        mock_platform_api.get(
            "/whatsapp/broadcasts", params={"page": "2", "per_page": "2"}
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_broadcast(id="3", name="c")],
                    "meta": {"page": 2, "per_page": 2, "total_pages": 2, "total_count": 3},
                },
            )
        )
        names = [b.name async for b in platform_client.broadcasts.iter(per_page=2)]
        assert names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestGet:
    async def test_unwraps_data(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c"
        mock_platform_api.get(f"/whatsapp/broadcasts/{broadcast_id}").mock(
            return_value=Response(
                200,
                json={"data": _broadcast(id=broadcast_id, status="sending")},
            )
        )
        result = await platform_client.broadcasts.get(broadcast_id)
        assert isinstance(result, Broadcast)
        assert result.id == broadcast_id
        assert result.status == "sending"


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_wraps_payload_in_whatsapp_broadcast_key(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/whatsapp/broadcasts").mock(
            return_value=Response(201, json={"data": _broadcast()})
        )
        result = await platform_client.broadcasts.create(
            name="Weekend Sale 2025",
            phone_number_id="1234567890",
            whatsapp_template_id="784203120908608",
        )
        assert isinstance(result, Broadcast)
        assert result.name == "Weekend Sale 2025"
        assert result.status == "draft"

        body = route.calls.last.request.read().decode()
        assert '"whatsapp_broadcast"' in body
        assert '"name":"Weekend Sale 2025"' in body
        assert '"phone_number_id":"1234567890"' in body
        assert '"whatsapp_template_id":"784203120908608"' in body


# ---------------------------------------------------------------------------
# list_recipients
# ---------------------------------------------------------------------------


class TestListRecipients:
    async def test_returns_recipient_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        mock_platform_api.get(
            f"/whatsapp/broadcasts/{broadcast_id}/recipients"
        ).mock(
            return_value=Response(
                200,
                json=_paginated(
                    [_recipient(), _recipient(id="r2", phone_number="14155550124")]
                ),
            )
        )
        results = await platform_client.broadcasts.list_recipients(broadcast_id)
        assert len(results) == 2
        assert all(isinstance(r, BroadcastRecipient) for r in results)
        assert results[0].phone_number == "14155550123"
        assert results[1].phone_number == "14155550124"

    async def test_passes_pagination_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        route = mock_platform_api.get(
            f"/whatsapp/broadcasts/{broadcast_id}/recipients"
        ).mock(return_value=Response(200, json=_paginated([])))
        await platform_client.broadcasts.list_recipients(
            broadcast_id, per_page=50, page=3
        )
        params = dict(route.calls.last.request.url.params)
        assert params["per_page"] == "50"
        assert params["page"] == "3"


# ---------------------------------------------------------------------------
# iter_recipients
# ---------------------------------------------------------------------------


class TestIterRecipients:
    async def test_iterates_all_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        bid = "abc-123"
        mock_platform_api.get(
            f"/whatsapp/broadcasts/{bid}/recipients",
            params={"page": "1", "per_page": "1"},
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_recipient(id="r1", phone_number="111")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get(
            f"/whatsapp/broadcasts/{bid}/recipients",
            params={"page": "2", "per_page": "1"},
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": [_recipient(id="r2", phone_number="222")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        phones = [
            r.phone_number
            async for r in platform_client.broadcasts.iter_recipients(bid, per_page=1)
        ]
        assert phones == ["111", "222"]


# ---------------------------------------------------------------------------
# add_recipients
# ---------------------------------------------------------------------------


class TestAddRecipients:
    async def test_wraps_payload_and_returns_result(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        route = mock_platform_api.post(
            f"/whatsapp/broadcasts/{broadcast_id}/recipients"
        ).mock(
            return_value=Response(
                201,
                json={"data": {"added": 2, "duplicates": 0, "errors": []}},
            )
        )
        recipients = [
            {"phone_number": "+14155550123", "components": []},
            {"phone_number": "+14155550124", "components": []},
        ]
        result = await platform_client.broadcasts.add_recipients(
            broadcast_id, recipients=recipients
        )
        assert isinstance(result, AddRecipientsResult)
        assert result.added == 2
        assert result.duplicates == 0
        assert result.errors == []

        body = route.calls.last.request.read().decode()
        assert '"whatsapp_broadcast"' in body
        assert '"recipients"' in body

    async def test_errors_field_populated(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        mock_platform_api.post(
            f"/whatsapp/broadcasts/{broadcast_id}/recipients"
        ).mock(
            return_value=Response(
                201,
                json={
                    "data": {
                        "added": 8,
                        "duplicates": 1,
                        "errors": ["Recipient 3: invalid phone number format"],
                    }
                },
            )
        )
        result = await platform_client.broadcasts.add_recipients(
            broadcast_id, recipients=[]
        )
        assert result.added == 8
        assert result.duplicates == 1
        assert len(result.errors) == 1


# ---------------------------------------------------------------------------
# send
# ---------------------------------------------------------------------------


class TestSend:
    async def test_posts_without_body_and_returns_action_result(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        route = mock_platform_api.post(
            f"/whatsapp/broadcasts/{broadcast_id}/send"
        ).mock(
            return_value=Response(
                202,
                json={"data": _action_result(status="sending")},
            )
        )
        result = await platform_client.broadcasts.send(broadcast_id)
        assert isinstance(result, BroadcastActionResult)
        assert result.status == "sending"
        # No request body should be sent
        body = route.calls.last.request.read().decode()
        assert body == "" or body == "null" or body == "{}"


# ---------------------------------------------------------------------------
# schedule
# ---------------------------------------------------------------------------


class TestSchedule:
    async def test_sends_scheduled_at_and_returns_action_result(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        route = mock_platform_api.post(
            f"/whatsapp/broadcasts/{broadcast_id}/schedule"
        ).mock(
            return_value=Response(
                202,
                json={
                    "data": _action_result(
                        status="scheduled",
                        scheduled_at="2025-10-12T17:00:00Z",
                        started_at=None,
                    )
                },
            )
        )
        result = await platform_client.broadcasts.schedule(
            broadcast_id, scheduled_at="2025-10-12T17:00:00Z"
        )
        assert isinstance(result, BroadcastActionResult)
        assert result.status == "scheduled"
        assert result.scheduled_at == "2025-10-12T17:00:00Z"

        body = route.calls.last.request.read().decode()
        assert '"scheduled_at"' in body
        assert "2025-10-12T17:00:00Z" in body
        # NOT wrapped in whatsapp_broadcast
        assert "whatsapp_broadcast" not in body


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


class TestCancel:
    async def test_posts_without_body_and_returns_draft_status(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        broadcast_id = "abc-123"
        mock_platform_api.post(
            f"/whatsapp/broadcasts/{broadcast_id}/cancel"
        ).mock(
            return_value=Response(
                200,
                json={
                    "data": _action_result(
                        status="draft",
                        scheduled_at=None,
                        started_at=None,
                    )
                },
            )
        )
        result = await platform_client.broadcasts.cancel(broadcast_id)
        assert isinstance(result, BroadcastActionResult)
        assert result.status == "draft"
        assert result.scheduled_at is None
