"""Tests for the Database Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient


def _row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "status": "active",
    }
    base.update(overrides)
    return base


class TestQuery:
    async def test_returns_list_of_rows(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/db/contacts").mock(
            return_value=Response(
                200,
                json={"data": [_row(), _row(id=2, name="Jane Smith")]},
            )
        )
        rows = await platform_client.database.query("contacts")
        assert len(rows) == 2
        assert rows[0]["name"] == "John Doe"
        assert rows[1]["name"] == "Jane Smith"

    async def test_passes_limit_and_offset(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/db/contacts").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.database.query("contacts", limit=50, offset=10)
        params = dict(route.calls.last.request.url.params)
        assert params["limit"] == "50"
        assert params["offset"] == "10"

    async def test_passes_select_and_order(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/db/contacts").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.database.query(
            "contacts", select="id,name", order="name.asc"
        )
        params = dict(route.calls.last.request.url.params)
        assert params["select"] == "id,name"
        assert params["order"] == "name.asc"

    async def test_passes_postgrest_filters(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/db/contacts").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.database.query("contacts", status="eq.active")
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "eq.active"

    async def test_returns_empty_list_when_no_data(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/db/contacts").mock(
            return_value=Response(200, json={"data": []})
        )
        rows = await platform_client.database.query("contacts")
        assert rows == []


class TestGet:
    async def test_returns_single_row(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/db/contacts/42").mock(
            return_value=Response(
                200, json={"data": _row(id=42, name="Alice")}
            )
        )
        row = await platform_client.database.get("contacts", "42")
        assert row["id"] == 42
        assert row["name"] == "Alice"

    async def test_uses_table_and_id_in_path(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/db/orders/abc-uuid").mock(
            return_value=Response(200, json={"data": {"id": "abc-uuid"}})
        )
        await platform_client.database.get("orders", "abc-uuid")
        assert "/db/orders/abc-uuid" in str(route.calls.last.request.url)


class TestInsert:
    async def test_single_row_sent_as_json(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/db/contacts").mock(
            return_value=Response(201, json={"data": [_row()]})
        )
        result = await platform_client.database.insert(
            "contacts", {"name": "John Doe", "email": "john@example.com"}
        )
        assert len(result) == 1
        body = route.calls.last.request.read().decode()
        assert '"name":"John Doe"' in body
        assert '"email":"john@example.com"' in body

    async def test_bulk_insert_sends_list(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/db/contacts").mock(
            return_value=Response(201, json={"data": [_row(), _row(id=2)]})
        )
        result = await platform_client.database.insert(
            "contacts",
            [
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Smith", "email": "jane@example.com"},
            ],
        )
        assert len(result) == 2
        body = route.calls.last.request.read().decode()
        assert "Jane Smith" in body


class TestUpsert:
    async def test_sends_put_request(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.put("/db/contacts").mock(
            return_value=Response(200, json={"data": [_row()]})
        )
        result = await platform_client.database.upsert(
            "contacts", {"id": 1, "name": "John Doe"}
        )
        assert len(result) == 1
        assert route.calls.last.request.method == "PUT"

    async def test_bulk_upsert_sends_list(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.put("/db/contacts").mock(
            return_value=Response(200, json={"data": [_row(), _row(id=2)]})
        )
        result = await platform_client.database.upsert(
            "contacts",
            [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}],
        )
        assert len(result) == 2


class TestUpdate:
    async def test_sends_patch_with_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch("/db/contacts").mock(
            return_value=Response(200, json={"data": [_row(status="inactive")]})
        )
        result = await platform_client.database.update(
            "contacts", {"status": "inactive"}
        )
        assert result[0]["status"] == "inactive"
        body = route.calls.last.request.read().decode()
        assert '"status":"inactive"' in body

    async def test_passes_filter_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch("/db/contacts").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.database.update(
            "contacts", {"status": "inactive"}, id="eq.1"
        )
        params = dict(route.calls.last.request.url.params)
        assert params["id"] == "eq.1"


class TestDelete:
    async def test_sends_delete_request(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.delete("/db/contacts").mock(
            return_value=Response(204)
        )
        result = await platform_client.database.delete("contacts")
        assert result is None
        assert route.calls.last.request.method == "DELETE"

    async def test_passes_filter_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.delete("/db/contacts").mock(
            return_value=Response(204)
        )
        await platform_client.database.delete("contacts", status="eq.inactive")
        params = dict(route.calls.last.request.url.params)
        assert params["status"] == "eq.inactive"
