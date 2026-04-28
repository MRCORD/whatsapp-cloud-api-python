"""
WebhookDeliveries resource for the Kapso Platform API.

Provides access to webhook delivery attempt records for the project.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/webhook-deliveries/list-webhook-deliveries
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource


class WebhookDelivery(BaseModel):
    """A webhook delivery attempt record."""

    id: str
    event: str
    status: str
    attempt_count: int
    created_at: str
    response_status: int | None = None
    delivered_at: str | None = None
    failed_at: str | None = None
    last_attempt_at: str | None = None
    webhook_id: str
    webhook_url: str
    whatsapp_config_id: str | None = None
    phone_number_id: str | None = None
    conversation_phone_number: str | None = None


class WebhookDeliveriesResource(PlatformBaseResource):
    """Access webhook delivery attempt records for your Kapso project.

    Path: GET /webhook_deliveries
    """

    async def list(
        self,
        *,
        status: str | None = None,
        event: str | None = None,
        webhook_id: str | None = None,
        errors_only: bool | None = None,
        period: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[WebhookDelivery]:
        """List webhook deliveries (single page). For full-iteration use `iter()`."""
        params = _filters(
            status=status,
            event=event,
            webhook_id=webhook_id,
            errors_only=errors_only,
            period=period,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "webhook_deliveries", params=params)
        return [WebhookDelivery.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        status: str | None = None,
        event: str | None = None,
        webhook_id: str | None = None,
        errors_only: bool | None = None,
        period: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[WebhookDelivery]:
        """Async iterator over every webhook delivery record matching the filters."""
        params = _filters(
            status=status,
            event=event,
            webhook_id=webhook_id,
            errors_only=errors_only,
            period=period,
        )
        async for row in self._client.paginate(
            "webhook_deliveries", params=params, per_page=per_page
        ):
            yield WebhookDelivery.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
