"""Tests for the provider_models Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.provider_models import ProviderModel

# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def _model(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
        "name": "gpt-4o",
        "provider": "openai",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/provider_models").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        _model(),
                        _model(
                            id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                            name="claude-3-sonnet",
                            provider="anthropic",
                        ),
                    ]
                },
            )
        )
        results = await platform_client.provider_models.list()
        assert len(results) == 2
        assert all(isinstance(m, ProviderModel) for m in results)
        assert results[0].name == "gpt-4o"
        assert results[0].provider == "openai"
        assert results[1].name == "claude-3-sonnet"
        assert results[1].provider == "anthropic"

    async def test_returns_empty_list(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/provider_models").mock(
            return_value=Response(200, json={"data": []})
        )
        results = await platform_client.provider_models.list()
        assert results == []

    async def test_model_fields_populated(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        model_id = "3c90c3cc-0d44-4b50-8888-8dd25736052a"
        mock_platform_api.get("/provider_models").mock(
            return_value=Response(
                200,
                json={"data": [_model(id=model_id)]},
            )
        )
        results = await platform_client.provider_models.list()
        m = results[0]
        assert m.id == model_id
        assert m.name == "gpt-4o"
        assert m.provider == "openai"

    async def test_no_query_params_sent(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/provider_models").mock(
            return_value=Response(200, json={"data": [_model()]})
        )
        await platform_client.provider_models.list()
        params = dict(route.calls.last.request.url.params)
        assert params == {}

    async def test_single_model(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/provider_models").mock(
            return_value=Response(200, json={"data": [_model()]})
        )
        results = await platform_client.provider_models.list()
        assert len(results) == 1
        assert isinstance(results[0], ProviderModel)


class TestDocExampleValidates:
    """Regression guard: doc example from
    docs.kapso.ai/api/platform/v1/provider-models/list-provider-models
    must remain parseable by ProviderModel without modification."""

    def test_provider_model_doc_example_validates(self) -> None:
        example = {
            "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "name": "<string>",
            "provider": "<string>",
        }
        ProviderModel.model_validate(example)  # raises if model gets stricter than docs
