"""Tests for the Integrations Platform resource."""

from __future__ import annotations

import respx
from httpx import Response

from kapso_whatsapp.platform import KapsoPlatformClient
from kapso_whatsapp.platform.resources.integrations import (
    AvailableAction,
    AvailableApp,
    ConnectedAccount,
    ConnectToken,
    Integration,
    IntegrationUser,
)


def _integration(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "action_id": "slack-send-message",
        "app_slug": "slack",
        "app_name": "Slack",
        "action_name": "Send Message",
        "name": "Notify Sales Channel",
        "enabled": True,
        "configured_props": {"channel": "#sales"},
        "variable_definitions": {},
        "dynamic_props_id": None,
        "metadata": {},
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "pipedream_account": {
            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "pipedream_account_id": "apn_abc123",
            "app_slug": "slack",
            "app_name": "Slack",
            "account_name": "My Workspace",
            "healthy": True,
            "created_at": "2025-01-10T08:00:00Z",
            "updated_at": "2025-01-10T08:00:00Z",
            "user": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "user@example.com",
                "name": "John Doe",
                "avatar_url": None,
                "created_at": "2025-01-01T00:00:00Z",
                "onboarding_status": "complete",
            },
            "project": None,
        },
    }
    base.update(overrides)
    return base


class TestList:
    async def test_returns_typed_models(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/integrations").mock(
            return_value=Response(
                200,
                json={"data": [_integration(), _integration(id="other-id", name="Other")]},
            )
        )
        items = await platform_client.integrations.list()
        assert len(items) == 2
        assert items[0].action_id == "slack-send-message"
        assert items[1].name == "Other"

    async def test_returns_empty_list(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/integrations").mock(
            return_value=Response(200, json={"data": []})
        )
        items = await platform_client.integrations.list()
        assert items == []


class TestCreate:
    async def test_sends_required_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/integrations").mock(
            return_value=Response(200, json={"data": _integration()})
        )
        result = await platform_client.integrations.create(
            action_id="slack-send-message",
            app_slug="slack",
        )
        assert result.action_id == "slack-send-message"
        body = route.calls.last.request.read().decode()
        assert '"action_id":"slack-send-message"' in body
        assert '"app_slug":"slack"' in body

    async def test_sends_optional_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/integrations").mock(
            return_value=Response(200, json={"data": _integration()})
        )
        await platform_client.integrations.create(
            action_id="slack-send-message",
            app_slug="slack",
            app_name="Slack",
            name="My Integration",
            configured_props={"channel": "#general"},
            variable_definitions={"msg": "string"},
        )
        body = route.calls.last.request.read().decode()
        assert '"app_name":"Slack"' in body
        assert '"name":"My Integration"' in body
        assert "#general" in body
        assert '"msg":"string"' in body

    async def test_omits_none_optional_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post("/integrations").mock(
            return_value=Response(200, json={"data": _integration()})
        )
        await platform_client.integrations.create(
            action_id="slack-send-message",
            app_slug="slack",
        )
        body = route.calls.last.request.read().decode()
        assert "app_name" not in body
        assert "dynamic_props_id" not in body


class TestUpdate:
    async def test_sends_patch_to_integration_id(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch(
            "/integrations/550e8400-e29b-41d4-a716-446655440000"
        ).mock(
            return_value=Response(
                200, json={"data": _integration(name="Updated Name")}
            )
        )
        result = await platform_client.integrations.update(
            "550e8400-e29b-41d4-a716-446655440000", name="Updated Name"
        )
        assert result.name == "Updated Name"
        body = route.calls.last.request.read().decode()
        assert '"name":"Updated Name"' in body

    async def test_omits_unprovided_fields(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.patch("/integrations/abc").mock(
            return_value=Response(200, json={"data": _integration()})
        )
        await platform_client.integrations.update("abc", name="Only Name")
        body = route.calls.last.request.read().decode()
        assert "configured_props" not in body
        assert "variable_definitions" not in body


class TestDelete:
    async def test_returns_success_dict(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.delete(
            "/integrations/550e8400-e29b-41d4-a716-446655440000"
        ).mock(
            return_value=Response(
                200, json={"data": {"success": True}}
            )
        )
        result = await platform_client.integrations.delete(
            "550e8400-e29b-41d4-a716-446655440000"
        )
        assert result == {"success": True}


class TestListApps:
    async def test_returns_available_apps(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/integrations/apps").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "app_1",
                            "name_slug": "slack",
                            "name": "Slack",
                            "description": "Team messaging",
                            "img_src": "https://example.com/slack.png",
                        }
                    ]
                },
            )
        )
        apps = await platform_client.integrations.list_apps()
        assert len(apps) == 1
        assert apps[0].name == "Slack"
        assert apps[0].name_slug == "slack"

    async def test_passes_query_and_limit(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/integrations/apps").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.integrations.list_apps(query="slack", limit=10)
        params = dict(route.calls.last.request.url.params)
        assert params["query"] == "slack"
        assert params["limit"] == "10"

    async def test_passes_filter_booleans(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/integrations/apps").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.integrations.list_apps(has_actions=True)
        params = dict(route.calls.last.request.url.params)
        assert params["has_actions"] in ("True", "true")


class TestListActions:
    async def test_returns_available_actions(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/integrations/actions").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "key": "slack-send-message",
                            "name": "Send Message",
                            "description": "Send a message to a channel",
                            "version": "0.4.0",
                        }
                    ]
                },
            )
        )
        actions = await platform_client.integrations.list_actions()
        assert len(actions) == 1
        assert actions[0].key == "slack-send-message"

    async def test_passes_app_slug_filter(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/integrations/actions").mock(
            return_value=Response(200, json={"data": []})
        )
        await platform_client.integrations.list_actions(app_slug="slack", query="send")
        params = dict(route.calls.last.request.url.params)
        assert params["app_slug"] == "slack"
        assert params["query"] == "send"


class TestListAccounts:
    async def test_returns_connected_accounts(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get("/integrations/accounts").mock(
            return_value=Response(
                200,
                json={
                    "accounts": [
                        {
                            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                            "pipedream_account_id": "apn_abc123",
                            "app_slug": "slack",
                            "app_name": "Slack",
                            "account_name": "My Workspace",
                            "healthy": True,
                            "created_at": "2025-01-10T08:00:00Z",
                            "updated_at": "2025-01-10T08:00:00Z",
                            "user": {
                                "id": "u1",
                                "email": "user@example.com",
                                "created_at": "2025-01-01T00:00:00Z",
                            },
                            "project": None,
                        }
                    ]
                },
            )
        )
        accounts = await platform_client.integrations.list_accounts()
        assert len(accounts) == 1
        assert accounts[0].app_slug == "slack"
        assert accounts[0].healthy is True

    async def test_passes_app_slug_filter(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get("/integrations/accounts").mock(
            return_value=Response(200, json={"accounts": []})
        )
        await platform_client.integrations.list_accounts(app_slug="slack")
        params = dict(route.calls.last.request.url.params)
        assert params["app_slug"] == "slack"


class TestGetConnectToken:
    async def test_returns_token_and_expiry(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.post("/integrations/connect_token").mock(
            return_value=Response(
                200,
                json={
                    "token": "pd_ct_abc123xyz",
                    "expires_at": "2025-01-15T10:15:00Z",
                },
            )
        )
        ct = await platform_client.integrations.get_connect_token()
        assert ct.token == "pd_ct_abc123xyz"
        assert ct.expires_at == "2025-01-15T10:15:00Z"


class TestGetActionSchema:
    async def test_returns_schema_dict(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        mock_platform_api.get(
            "/integrations/actions/slack-send-message/schema"
        ).mock(
            return_value=Response(
                200,
                json={"data": {"props": {"channel": {"type": "string"}}}},
            )
        )
        schema = await platform_client.integrations.get_action_schema(
            "slack-send-message"
        )
        assert "props" in schema

    async def test_uses_action_id_in_path(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.get(
            "/integrations/actions/my-action/schema"
        ).mock(return_value=Response(200, json={"data": {}}))
        await platform_client.integrations.get_action_schema("my-action")
        assert "/integrations/actions/my-action/schema" in str(
            route.calls.last.request.url
        )


class TestConfigureActionProp:
    async def test_sends_prop_name_and_configured_props(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            "/integrations/actions/slack-send-message/configure_prop"
        ).mock(
            return_value=Response(
                200, json={"data": [{"label": "#general", "value": "C012345"}]}
            )
        )
        result = await platform_client.integrations.configure_action_prop(
            "slack-send-message",
            prop_name="channel",
            configured_props={"slack": {"authProvisionId": "apn_abc123"}},
        )
        assert len(result) == 1
        body = route.calls.last.request.read().decode()
        assert '"prop_name":"channel"' in body
        assert "authProvisionId" in body

    async def test_omits_optional_dynamic_props_id(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            "/integrations/actions/slack-send-message/configure_prop"
        ).mock(return_value=Response(200, json={"data": []}))
        await platform_client.integrations.configure_action_prop(
            "slack-send-message", prop_name="channel"
        )
        body = route.calls.last.request.read().decode()
        assert "dynamic_props_id" not in body


class TestReloadActionProps:
    async def test_sends_configured_props_and_dynamic_props_id(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            "/integrations/actions/slack-send-message/reload_props"
        ).mock(return_value=Response(200, json={"data": [{}]}))
        result = await platform_client.integrations.reload_action_props(
            "slack-send-message",
            configured_props={"slack": {"authProvisionId": "apn_abc123"}},
            dynamic_props_id="dpi_xyz789",
        )
        assert isinstance(result, list)
        body = route.calls.last.request.read().decode()
        assert "dpi_xyz789" in body
        assert "authProvisionId" in body

    async def test_sends_empty_payload_when_no_args(
        self,
        platform_client: KapsoPlatformClient,
        mock_platform_api: respx.MockRouter,
    ) -> None:
        route = mock_platform_api.post(
            "/integrations/actions/my-action/reload_props"
        ).mock(return_value=Response(200, json={"data": []}))
        await platform_client.integrations.reload_action_props("my-action")
        body = route.calls.last.request.read().decode()
        assert body == "{}"


class TestDocExampleValidates:
    """Regression tests: each Pydantic model validates the exact JSON example
    shown in the Kapso docs (docs.kapso.ai/api/platform/v1/integrations/*).
    Failures here mean the live API changed its shape or the model drifted.
    """

    def test_integration_user_doc_example_validates(self) -> None:
        # Embedded inside list-connected-accounts and list-integrations responses.
        example = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "email": "user@example.com",
            "name": "John Doe",
            "avatar_url": None,
            "created_at": "2025-01-01T00:00:00Z",
            "onboarding_status": "complete",
        }
        IntegrationUser.model_validate(example)

    def test_connected_account_doc_example_validates(self) -> None:
        # From: GET /integrations/accounts (list-connected-accounts)
        example = {
            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "pipedream_account_id": "apn_abc123",
            "app_slug": "slack",
            "app_name": "Slack",
            "account_name": "My Workspace",
            "healthy": True,
            "created_at": "2025-01-10T08:00:00Z",
            "updated_at": "2025-01-10T08:00:00Z",
            "user": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "user@example.com",
                "name": "John Doe",
                "avatar_url": None,
                "created_at": "2025-01-01T00:00:00Z",
                "onboarding_status": "complete",
            },
            "project": None,
        }
        ConnectedAccount.model_validate(example)

    def test_connected_account_project_dict_validates(self) -> None:
        # create/update-integration docs show project as {} (non-null dict).
        example = {
            "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "pipedream_account_id": "<string>",
            "app_slug": "<string>",
            "healthy": True,
            "created_at": "2023-11-07T05:31:56Z",
            "updated_at": "2023-11-07T05:31:56Z",
            "app_name": "<string>",
            "account_name": "<string>",
            "user": {
                "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
                "email": "jsmith@example.com",
                "name": "<string>",
                "avatar_url": "<string>",
                "created_at": "2023-11-07T05:31:56Z",
                "onboarding_status": "<string>",
            },
            "project": {},
        }
        ConnectedAccount.model_validate(example)

    def test_integration_list_doc_example_validates(self) -> None:
        # From: GET /integrations (list-integrations) — full nested object.
        example = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "action_id": "slack-send-message",
            "app_slug": "slack",
            "app_name": "Slack",
            "action_name": "Send Message",
            "name": "Notify Sales Channel",
            "enabled": True,
            "configured_props": {"channel": "#sales"},
            "variable_definitions": {},
            "dynamic_props_id": None,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:00Z",
            "pipedream_account": {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "pipedream_account_id": "apn_abc123",
                "app_slug": "slack",
                "app_name": "Slack",
                "account_name": "My Workspace",
                "healthy": True,
                "created_at": "2025-01-10T08:00:00Z",
                "updated_at": "2025-01-10T08:00:00Z",
                "user": {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "avatar_url": None,
                    "created_at": "2025-01-01T00:00:00Z",
                    "onboarding_status": "complete",
                },
                "project": None,
            },
        }
        Integration.model_validate(example)

    def test_integration_create_doc_example_validates(self) -> None:
        # From: POST /integrations (create-integration) — dynamic_props_id is a
        # non-null string and project is an empty dict in this variant.
        example = {
            "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
            "action_id": "<string>",
            "app_slug": "<string>",
            "enabled": True,
            "created_at": "2023-11-07T05:31:56Z",
            "updated_at": "2023-11-07T05:31:56Z",
            "app_name": "<string>",
            "action_name": "<string>",
            "name": "<string>",
            "metadata": {},
            "configured_props": {},
            "variable_definitions": {},
            "dynamic_props_id": "<string>",
            "pipedream_account": {
                "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
                "pipedream_account_id": "<string>",
                "app_slug": "<string>",
                "healthy": True,
                "created_at": "2023-11-07T05:31:56Z",
                "updated_at": "2023-11-07T05:31:56Z",
                "app_name": "<string>",
                "account_name": "<string>",
                "user": {
                    "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
                    "email": "jsmith@example.com",
                    "name": "<string>",
                    "avatar_url": "<string>",
                    "created_at": "2023-11-07T05:31:56Z",
                    "onboarding_status": "<string>",
                },
                "project": {},
            },
        }
        Integration.model_validate(example)

    def test_available_app_doc_example_validates(self) -> None:
        # From: GET /integrations/apps (list-available-apps)
        example = {
            "id": "<string>",
            "name_slug": "<string>",
            "name": "<string>",
            "description": "<string>",
            "img_src": "<string>",
        }
        AvailableApp.model_validate(example)

    def test_available_action_doc_example_validates(self) -> None:
        # From: GET /integrations/actions (list-available-actions)
        example = {
            "key": "<string>",
            "name": "<string>",
            "description": "<string>",
            "version": "<string>",
        }
        AvailableAction.model_validate(example)

    def test_connect_token_doc_example_validates(self) -> None:
        # From: POST /integrations/connect_token (get-connect-token)
        example = {
            "token": "pd_ct_abc123xyz",
            "expires_at": "2025-01-15T10:15:00Z",
        }
        ConnectToken.model_validate(example)
