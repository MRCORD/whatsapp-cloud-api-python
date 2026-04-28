"""
ProjectWebhooks resource for the Kapso Platform API.

Manages project-scoped and phone-number-scoped webhooks via the
/whatsapp/webhooks/* family of endpoints. These are distinct from
the phone-number-nested /whatsapp/phone_numbers/{id}/webhooks/* endpoints
which are handled by WebhooksResource.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/webhooks/list-project-webhooks
  https://docs.kapso.ai/api/platform/v1/webhooks/create-project-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/get-project-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/delete-project-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/update-project-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/test-project-webhook
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource


class ProjectWebhook(BaseModel):
    """A project-scoped or phone-number-scoped webhook object."""

    model_config = ConfigDict(extra="allow")

    id: str
    url: str | None = None
    kind: str | None = None
    events: list[str] = []
    active: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    project_id: str | None = None
    phone_number_id: str | None = None
    secret_key: str | None = None
    headers: dict[str, Any] = {}
    buffer_enabled: bool | None = None
    buffer_window_seconds: int | None = None
    max_buffer_size: int | None = None
    buffer_events: list[str] = []
    inactivity_minutes: int | None = None
    payload_version: str | None = None


class WebhookTestResult(BaseModel):
    """Result of testing a project webhook."""

    success: bool


class ProjectWebhooksResource(PlatformBaseResource):
    """Manage project-level webhooks on your Kapso project.

    Path family: GET/POST/PATCH/DELETE /whatsapp/webhooks/{webhook_id}
    """

    async def list(
        self,
        *,
        kind: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[ProjectWebhook]:
        """List project webhooks (single page). For full-iteration use `iter()`."""
        params = _filters(kind=kind, per_page=per_page, page=page)
        rows = await self._request("GET", "whatsapp/webhooks", params=params)
        return [ProjectWebhook.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        kind: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[ProjectWebhook]:
        """Async iterator over every project webhook matching the filters."""
        params = _filters(kind=kind)
        async for row in self._client.paginate(
            "whatsapp/webhooks", params=params, per_page=per_page
        ):
            yield ProjectWebhook.model_validate(row)

    async def get(self, webhook_id: str) -> ProjectWebhook:
        """Fetch a single project webhook by id."""
        row = await self._request("GET", f"whatsapp/webhooks/{webhook_id}")
        return ProjectWebhook.model_validate(row)

    async def create(
        self,
        *,
        url: str,
        events: list[str],  # type: ignore[valid-type]
        secret_key: str | None = None,
        phone_number_id: str | None = None,
        active: bool | None = None,
        headers: dict[str, Any] | None = None,
        buffer_enabled: bool | None = None,
        buffer_window_seconds: int | None = None,
        max_buffer_size: int | None = None,
        buffer_events: list[str] | None = None,  # type: ignore[valid-type]
        inactivity_minutes: int | None = None,
        payload_version: str | None = None,
    ) -> ProjectWebhook:
        """Create a new project webhook."""
        payload: dict[str, Any] = {"url": url, "events": events}
        if secret_key is not None:
            payload["secret_key"] = secret_key
        if phone_number_id is not None:
            payload["phone_number_id"] = phone_number_id
        if active is not None:
            payload["active"] = active
        if headers is not None:
            payload["headers"] = headers
        if buffer_enabled is not None:
            payload["buffer_enabled"] = buffer_enabled
        if buffer_window_seconds is not None:
            payload["buffer_window_seconds"] = buffer_window_seconds
        if max_buffer_size is not None:
            payload["max_buffer_size"] = max_buffer_size
        if buffer_events is not None:
            payload["buffer_events"] = buffer_events
        if inactivity_minutes is not None:
            payload["inactivity_minutes"] = inactivity_minutes
        if payload_version is not None:
            payload["payload_version"] = payload_version
        row = await self._request(
            "POST", "whatsapp/webhooks", json={"whatsapp_webhook": payload}
        )
        return ProjectWebhook.model_validate(row)

    async def update(
        self,
        webhook_id: str,
        *,
        url: str | None = None,
        events: list[str] | None = None,  # type: ignore[valid-type]
        secret_key: str | None = None,
        active: bool | None = None,
        headers: dict[str, Any] | None = None,
        buffer_enabled: bool | None = None,
        buffer_window_seconds: int | None = None,
        max_buffer_size: int | None = None,
        buffer_events: list[str] | None = None,  # type: ignore[valid-type]
        inactivity_minutes: int | None = None,
        payload_version: str | None = None,
    ) -> ProjectWebhook:
        """Partial update — only fields you pass are sent."""
        payload: dict[str, Any] = {}
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = events
        if secret_key is not None:
            payload["secret_key"] = secret_key
        if active is not None:
            payload["active"] = active
        if headers is not None:
            payload["headers"] = headers
        if buffer_enabled is not None:
            payload["buffer_enabled"] = buffer_enabled
        if buffer_window_seconds is not None:
            payload["buffer_window_seconds"] = buffer_window_seconds
        if max_buffer_size is not None:
            payload["max_buffer_size"] = max_buffer_size
        if buffer_events is not None:
            payload["buffer_events"] = buffer_events
        if inactivity_minutes is not None:
            payload["inactivity_minutes"] = inactivity_minutes
        if payload_version is not None:
            payload["payload_version"] = payload_version
        row = await self._request(
            "PATCH",
            f"whatsapp/webhooks/{webhook_id}",
            json={"whatsapp_webhook": payload},
        )
        return ProjectWebhook.model_validate(row)

    async def delete(self, webhook_id: str) -> None:
        """Delete a project webhook."""
        await self._request("DELETE", f"whatsapp/webhooks/{webhook_id}")

    async def test(
        self,
        webhook_id: str,
        *,
        event_type: str | None = None,
    ) -> WebhookTestResult:
        """Send a test payload to the webhook endpoint.

        Optionally specify an event_type to test with a specific event payload.
        The event type must be one of the events the webhook is configured to receive.
        """
        payload: dict[str, Any] = {}
        if event_type is not None:
            payload["event_type"] = event_type
        row = await self._request(
            "POST",
            f"whatsapp/webhooks/{webhook_id}/test",
            json=payload,
        )
        return WebhookTestResult.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
