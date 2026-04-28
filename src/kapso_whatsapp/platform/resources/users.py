"""
Users resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/users/*

  GET /users  — list project users
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ProjectUser(BaseModel):
    """A user who is a member of the Kapso project."""

    model_config = ConfigDict(extra="allow")

    id: str
    user_id: str | None = None
    email: str | None = None
    name: str | None = None
    role: str | None = None


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class UsersResource(PlatformBaseResource):
    """List users who are members of the Kapso project."""

    async def list(
        self,
        *,
        per_page: int = 20,
        page: int = 1,
    ) -> list[ProjectUser]:
        """List project users (single page). Use `iter()` for full iteration."""
        params = _filters(per_page=per_page, page=page)
        rows = await self._request("GET", "users", params=params)
        return [ProjectUser.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        per_page: int = 20,
    ) -> AsyncIterator[ProjectUser]:
        """Async iterator over every project user."""
        async for row in self._client.paginate("users", per_page=per_page):
            yield ProjectUser.model_validate(row)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
