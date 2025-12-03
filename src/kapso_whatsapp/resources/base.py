"""Base resource class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import WhatsAppClient


class BaseResource:
    """Base class for API resources."""

    def __init__(self, client: WhatsAppClient) -> None:
        """
        Initialize resource.

        Args:
            client: Parent WhatsAppClient instance
        """
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make request through client."""
        return await self._client.request(method, path, **kwargs)

    def _require_kapso_proxy(self) -> None:
        """Raise error if not using Kapso proxy."""
        if not self._client.is_kapso_proxy():
            from ..exceptions import KapsoProxyRequiredError
            raise KapsoProxyRequiredError()
