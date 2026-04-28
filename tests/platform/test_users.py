"""Tests for the users Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient


def _user(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "0b36b2df-a351-40b2-90e8-ff6bd79585ac",
        "user_id": "f1e2d3c4-b5a6-9870-fedc-ba0987654321",
        "email": "owner@example.com",
        "name": "Owner User",
        "role": "owner",
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/users").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        _user(),
                        _user(id="22222222-2222-2222-2222-222222222222", user_id="e2d3c4b5-a697-8076-edcb-a09876543210",
                              email="member@example.com", name="Member User", role="member"),
                    ],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        result = await platform_client.users.list()
        assert len(result) == 2
        assert result[0].name == "Owner User"
        assert result[0].role == "owner"
        assert result[1].name == "Member User"
        assert result[1].role == "member"

    async def test_passes_pagination_params(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/users").mock(
            return_value=Response(
                200,
                json={"data": [], "meta": {"page": 2, "per_page": 10, "total_pages": 1, "total_count": 0}},
            )
        )
        await platform_client.users.list(per_page=10, page=2)
        params = dict(route.calls.last.request.url.params)
        assert params["per_page"] == "10"
        assert params["page"] == "2"

    async def test_model_fields_are_correct_types(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/users").mock(
            return_value=Response(
                200,
                json={
                    "data": [_user()],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 1},
                },
            )
        )
        result = await platform_client.users.list()
        user = result[0]
        # id is integer in the API response
        assert isinstance(user.id, str)
        assert isinstance(user.user_id, str)
        assert isinstance(user.email, str)


class TestIter:
    async def test_iterates_across_pages(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/users", params={"page": "1", "per_page": "1"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_user(id="11111111-1111-1111-1111-111111111111", name="Alice")],
                    "meta": {"page": 1, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        mock_platform_api.get("/users", params={"page": "2", "per_page": "1"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_user(id="22222222-2222-2222-2222-222222222222", name="Bob", role="member")],
                    "meta": {"page": 2, "per_page": 1, "total_pages": 2, "total_count": 2},
                },
            )
        )
        names = [u.name async for u in platform_client.users.iter(per_page=1)]
        assert names == ["Alice", "Bob"]

    async def test_iter_single_page(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/users", params={"page": "1", "per_page": "20"}).mock(
            return_value=Response(
                200,
                json={
                    "data": [_user(), _user(id="22222222-2222-2222-2222-222222222222", name="Bob", role="member")],
                    "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 2},
                },
            )
        )
        users = [u async for u in platform_client.users.iter()]
        assert len(users) == 2
        assert users[0].email == "owner@example.com"


class TestDocExampleValidates:
    """Regression guard: the live API response (verified via examples/platform_smoke.py
    against api.kapso.ai) must remain parseable by ProjectUser without modification.

    NOTE: The published doc example uses integer `id` placeholders (e.g. `1`), but the
    real API returns UUID strings (we hit it live during v0.2.0 smoke and got:
    `id="0b36b2df-..."`). The test below uses the live shape, not the doc placeholder.
    If this fails, the model became stricter than the live API allows."""

    def test_project_user_live_example_validates(self) -> None:
        from kapso_whatsapp.platform.resources.users import ProjectUser

        example = {
            "id": "0b36b2df-a351-40b2-90e8-ff6bd79585ac",
            "user_id": "f1e2d3c4-b5a6-9870-fedc-ba0987654321",
            "email": "owner@example.com",
            "name": "Owner User",
            "role": "owner",
        }
        ProjectUser.model_validate(example)  # currently raises — model rejects int id
