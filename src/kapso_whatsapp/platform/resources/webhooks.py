"""
Webhooks resource for the Kapso Platform API.

Manages phone-number-scoped webhooks via the
/whatsapp/phone_numbers/{phone_number_id}/webhooks/* family of endpoints.
These are distinct from the project-level /whatsapp/webhooks/* endpoints
which are handled by ProjectWebhooksResource.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/webhooks/list-webhooks
  https://docs.kapso.ai/api/platform/v1/webhooks/create-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/get-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/delete-webhook
  https://docs.kapso.ai/api/platform/v1/webhooks/update-webhook
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource


class Webhook(BaseModel):
    """A phone-number-scoped webhook object."""

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


class WebhooksResource(PlatformBaseResource):
    """Manage phone-number-scoped webhooks on your Kapso project.

    All methods require a phone_number_id that scopes the webhook to a
    specific WhatsApp number.

    Path family:
      GET/POST /whatsapp/phone_numbers/{phone_number_id}/webhooks
      GET/PATCH/DELETE /whatsapp/phone_numbers/{phone_number_id}/webhooks/{webhook_id}
    """

    async def list(
        self,
        phone_number_id: str,
        *,
        url_contains: str | None = None,
        kind: str | None = None,
        active: bool | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Webhook]:
        """List webhooks for a phone number (single page). For full-iteration use `iter()`."""
        params = _filters(
            url_contains=url_contains,
            kind=kind,
            active=active,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks"
        rows = await self._request("GET", path, params=params)
        return [Webhook.model_validate(r) for r in rows]

    async def iter(
        self,
        phone_number_id: str,
        *,
        url_contains: str | None = None,
        kind: str | None = None,
        active: bool | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Webhook]:
        """Async iterator over every webhook for a phone number matching the filters."""
        params = _filters(
            url_contains=url_contains,
            kind=kind,
            active=active,
            created_after=created_after,
            created_before=created_before,
        )
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks"
        async for row in self._client.paginate(path, params=params, per_page=per_page):
            yield Webhook.model_validate(row)

    async def get(self, phone_number_id: str, webhook_id: str) -> Webhook:
        """Fetch a single webhook by id for a given phone number."""
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks/{webhook_id}"
        row = await self._request("GET", path)
        return Webhook.model_validate(row)

    async def create(
        self,
        phone_number_id: str,
        *,
        url: str,
        events: list[str],  # type: ignore[valid-type]
        secret_key: str | None = None,
        active: bool | None = None,
        headers: dict[str, Any] | None = None,
        buffer_enabled: bool | None = None,
        buffer_window_seconds: int | None = None,
        max_buffer_size: int | None = None,
        buffer_events: list[str] | None = None,  # type: ignore[valid-type]
        inactivity_minutes: int | None = None,
        payload_version: str | None = None,
    ) -> Webhook:
        """Create a new webhook for a phone number."""
        payload: dict[str, Any] = {"url": url, "events": events}
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
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks"
        row = await self._request(
            "POST", path, json={"whatsapp_webhook": payload}
        )
        return Webhook.model_validate(row)

    async def update(
        self,
        phone_number_id: str,
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
    ) -> Webhook:
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
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks/{webhook_id}"
        row = await self._request(
            "PATCH", path, json={"whatsapp_webhook": payload}
        )
        return Webhook.model_validate(row)

    async def delete(self, phone_number_id: str, webhook_id: str) -> None:
        """Delete a webhook for a phone number."""
        path = f"whatsapp/phone_numbers/{phone_number_id}/webhooks/{webhook_id}"
        await self._request("DELETE", path)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
