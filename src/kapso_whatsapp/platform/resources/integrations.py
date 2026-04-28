"""
Integrations resource for the Kapso Platform API.

Manages Pipedream-backed integrations: CRUD on saved integrations plus
sub-resource helpers for apps, actions, connected accounts, and dynamic
prop configuration.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/integrations/*
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class IntegrationUser(BaseModel):
    id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None
    created_at: str
    onboarding_status: str | None = None


class ConnectedAccount(BaseModel):
    id: str
    pipedream_account_id: str
    app_slug: str
    app_name: str | None = None
    account_name: str | None = None
    healthy: bool
    created_at: str
    updated_at: str
    user: IntegrationUser | None = None
    project: dict[str, Any] | None = None


class Integration(BaseModel):
    id: str
    action_id: str
    app_slug: str
    app_name: str | None = None
    action_name: str | None = None
    name: str | None = None
    enabled: bool
    configured_props: dict[str, Any] | None = None
    variable_definitions: dict[str, Any] | None = None
    dynamic_props_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: str
    updated_at: str
    pipedream_account: ConnectedAccount | None = None


class AvailableApp(BaseModel):
    id: str | None = None
    name_slug: str | None = None
    name: str | None = None
    description: str | None = None
    img_src: str | None = None


class AvailableAction(BaseModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None


class ConnectToken(BaseModel):
    token: str
    expires_at: str


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class IntegrationsResource(PlatformBaseResource):
    """Manage Pipedream integrations on your Kapso project."""

    # ------------------------------------------------------------------
    # CRUD — saved integrations
    # ------------------------------------------------------------------

    async def list(self) -> list[Integration]:
        """List all saved integrations (GET /integrations)."""
        rows = await self._request("GET", "integrations")
        if isinstance(rows, list):
            return [Integration.model_validate(r) for r in rows]
        return []

    async def create(
        self,
        *,
        action_id: str,
        app_slug: str,
        app_name: str | None = None,
        name: str | None = None,
        configured_props: dict[str, Any] | None = None,
        variable_definitions: dict[str, Any] | None = None,
        dynamic_props_id: str | None = None,
    ) -> Integration:
        """
        Save a configured Pipedream action as an integration
        (POST /integrations).
        """
        payload: dict[str, Any] = {
            "action_id": action_id,
            "app_slug": app_slug,
        }
        if app_name is not None:
            payload["app_name"] = app_name
        if name is not None:
            payload["name"] = name
        if configured_props is not None:
            payload["configured_props"] = configured_props
        if variable_definitions is not None:
            payload["variable_definitions"] = variable_definitions
        if dynamic_props_id is not None:
            payload["dynamic_props_id"] = dynamic_props_id

        row = await self._request("POST", "integrations", json=payload)
        return Integration.model_validate(row)

    async def update(
        self,
        integration_id: str,
        *,
        name: str | None = None,
        configured_props: dict[str, Any] | None = None,
        variable_definitions: dict[str, Any] | None = None,
        dynamic_props_id: str | None = None,
    ) -> Integration:
        """
        Partial update of a saved integration
        (PATCH /integrations/{integration_id}).
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if configured_props is not None:
            payload["configured_props"] = configured_props
        if variable_definitions is not None:
            payload["variable_definitions"] = variable_definitions
        if dynamic_props_id is not None:
            payload["dynamic_props_id"] = dynamic_props_id

        row = await self._request(
            "PATCH",
            f"integrations/{integration_id}",
            json=payload,
        )
        return Integration.model_validate(row)

    async def delete(self, integration_id: str) -> dict[str, Any]:
        """
        Delete a saved integration (DELETE /integrations/{integration_id}).

        Returns the raw ``{"success": true}`` dict from the API.
        """
        result = await self._request("DELETE", f"integrations/{integration_id}")
        if isinstance(result, dict):
            return result
        return {}

    # ------------------------------------------------------------------
    # Apps catalog
    # ------------------------------------------------------------------

    async def list_apps(
        self,
        *,
        query: str | None = None,
        has_components: bool | None = None,
        has_actions: bool | None = None,
        has_triggers: bool | None = None,
        limit: int = 50,
    ) -> list[AvailableApp]:  # type: ignore[valid-type]
        """
        Search Pipedream's app catalog (GET /integrations/apps).

        Args:
            query:          Search by app name.
            has_components: Only return apps with components.
            has_actions:    Only return apps with actions.
            has_triggers:   Only return apps with triggers.
            limit:          Maximum results (default 50).
        """
        params = _filters(
            query=query,
            has_components=has_components,
            has_actions=has_actions,
            has_triggers=has_triggers,
            limit=limit,
        )
        rows = await self._request("GET", "integrations/apps", params=params)
        if isinstance(rows, list):
            return [AvailableApp.model_validate(r) for r in rows]
        return []

    # ------------------------------------------------------------------
    # Actions catalog
    # ------------------------------------------------------------------

    async def list_actions(
        self,
        *,
        app_slug: str | None = None,
        query: str | None = None,
    ) -> list[AvailableAction]:  # type: ignore[valid-type]
        """
        List Pipedream actions for an app (GET /integrations/actions).

        Args:
            app_slug: Filter by app slug (e.g. "slack").
            query:    Free-text search across action names/descriptions.
        """
        params = _filters(app_slug=app_slug, query=query)
        rows = await self._request("GET", "integrations/actions", params=params)
        if isinstance(rows, list):
            return [AvailableAction.model_validate(r) for r in rows]
        return []

    # ------------------------------------------------------------------
    # Connected accounts
    # ------------------------------------------------------------------

    async def list_accounts(
        self,
        *,
        app_slug: str | None = None,
    ) -> list[ConnectedAccount]:  # type: ignore[valid-type]
        """
        Get Pipedream accounts connected to this project
        (GET /integrations/accounts).

        Args:
            app_slug: Filter by app slug (e.g. "slack").
        """
        params = _filters(app_slug=app_slug)
        envelope = await self._client.request_raw(
            "GET", "integrations/accounts", params=params or None
        )
        # NOTE: this endpoint returns {"accounts": [...]} instead of {"data": [...]}
        rows = envelope.get("accounts") or []
        return [ConnectedAccount.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Connect token
    # ------------------------------------------------------------------

    async def get_connect_token(self) -> ConnectToken:
        """
        Generate a short-lived token for the Pipedream Connect OAuth flow
        (POST /integrations/connect_token).
        """
        # Response is NOT wrapped in {"data": ...} — it is the raw object.
        envelope = await self._client.request_raw("POST", "integrations/connect_token")
        # The envelope itself is the token object (token + expires_at).
        return ConnectToken.model_validate(envelope)

    # ------------------------------------------------------------------
    # Action schema
    # ------------------------------------------------------------------

    async def get_action_schema(self, action_id: str) -> dict[str, Any]:
        """
        Get the configuration schema for a Pipedream action
        (GET /integrations/actions/{action_id}/schema).

        Args:
            action_id: Pipedream action ID (e.g. "slack-send-message").

        Returns:
            Schema dict (structure varies by action).
        """
        result = await self._request(
            "GET", f"integrations/actions/{action_id}/schema"
        )
        if isinstance(result, dict):
            return result
        return {}

    # ------------------------------------------------------------------
    # Configure action prop
    # ------------------------------------------------------------------

    async def configure_action_prop(
        self,
        action_id: str,
        *,
        prop_name: str,
        configured_props: dict[str, Any] | None = None,
        dynamic_props_id: str | None = None,
    ) -> list[dict[str, Any]]:  # type: ignore[valid-type]
        """
        Get dynamic options for an action prop based on current configuration
        (POST /integrations/actions/{action_id}/configure_prop).

        Args:
            action_id:        Pipedream action ID.
            prop_name:        Name of the prop to configure.
            configured_props: Current prop values (e.g. auth provision IDs).
            dynamic_props_id: Dynamic props session ID.

        Returns:
            List of option dicts for the requested prop.
        """
        payload: dict[str, Any] = {"prop_name": prop_name}
        if configured_props is not None:
            payload["configured_props"] = configured_props
        if dynamic_props_id is not None:
            payload["dynamic_props_id"] = dynamic_props_id

        result = await self._request(
            "POST",
            f"integrations/actions/{action_id}/configure_prop",
            json=payload,
        )
        if isinstance(result, list):
            return result
        return []

    # ------------------------------------------------------------------
    # Reload action props
    # ------------------------------------------------------------------

    async def reload_action_props(
        self,
        action_id: str,
        *,
        configured_props: dict[str, Any] | None = None,
        dynamic_props_id: str | None = None,
    ) -> list[dict[str, Any]]:  # type: ignore[valid-type]
        """
        Reload dynamic props for an action after configuration changes
        (POST /integrations/actions/{action_id}/reload_props).

        Args:
            action_id:        Pipedream action ID.
            configured_props: Current prop values.
            dynamic_props_id: Dynamic props session ID to reload.

        Returns:
            List of refreshed prop dicts.
        """
        payload: dict[str, Any] = {}
        if configured_props is not None:
            payload["configured_props"] = configured_props
        if dynamic_props_id is not None:
            payload["dynamic_props_id"] = dynamic_props_id

        result = await self._request(
            "POST",
            f"integrations/actions/{action_id}/reload_props",
            json=payload,
        )
        if isinstance(result, list):
            return result
        return []


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
