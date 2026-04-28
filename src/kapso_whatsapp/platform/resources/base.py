"""Base resource for Platform API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import KapsoPlatformClient


class PlatformBaseResource:
    """
    Base class for Platform API resources.

    Resources access the parent client via `self._client` and call
    `self._client.request(...)` (unwrapped data) or
    `self._client.request_raw(...)` (full envelope with meta).
    """

    def __init__(self, client: KapsoPlatformClient) -> None:
        self._client = client

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Call client.request and return unwrapped data."""
        return await self._client.request(method, path, **kwargs)

    async def _request_raw(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Call client.request_raw and return the full envelope."""
        return await self._client.request_raw(method, path, **kwargs)
