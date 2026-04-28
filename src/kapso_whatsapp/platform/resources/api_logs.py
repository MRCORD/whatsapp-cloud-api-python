"""
ApiLogs resource for the Kapso Platform API.

Provides access to API request log records for the project.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/api-logs/list-api-logs
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from .base import PlatformBaseResource


class ApiLog(BaseModel):
    """An API request log entry."""

    id: str
    endpoint: str
    http_method: str
    response_status: int
    response_time_ms: int
    created_at: str
    ip_address: str | None = None
    error_message: str | None = None
    api_key_id: str | None = None
    api_key_name: str | None = None


class ApiLogsResource(PlatformBaseResource):
    """Access API request logs for your Kapso project.

    Path: GET /api_logs
    """

    async def list(
        self,
        *,
        endpoint: str | None = None,
        status_code: int | None = None,
        errors_only: bool | None = None,
        period: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[ApiLog]:
        """List API logs (single page). For full-iteration use `iter()`."""
        params = _filters(
            endpoint=endpoint,
            status_code=status_code,
            errors_only=errors_only,
            period=period,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "api_logs", params=params)
        return [ApiLog.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        endpoint: str | None = None,
        status_code: int | None = None,
        errors_only: bool | None = None,
        period: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[ApiLog]:
        """Async iterator over every API log entry matching the filters."""
        params = _filters(
            endpoint=endpoint,
            status_code=status_code,
            errors_only=errors_only,
            period=period,
        )
        async for row in self._client.paginate(
            "api_logs", params=params, per_page=per_page
        ):
            yield ApiLog.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
