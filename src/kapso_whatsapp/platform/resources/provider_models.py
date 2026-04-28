"""
Provider Models resource for the Kapso Platform API.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/provider-models/list-provider-models

Returns available AI provider models (not paginated — the API returns a flat
``data`` array with no ``meta`` envelope).

Public methods:
  * list() — fetch all provider models (returns list[ProviderModel])
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .base import PlatformBaseResource

# =============================================================================
# Models
# =============================================================================


class ProviderModel(BaseModel):
    """An AI provider model available in the Kapso platform."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    provider: str


# =============================================================================
# Resource
# =============================================================================


class ProviderModelsResource(PlatformBaseResource):
    """Query AI provider models available on your Kapso project."""

    async def list(self) -> list[ProviderModel]:
        """Return all available AI provider models.

        The endpoint is not paginated — the full list is returned in a single
        request.
        """
        rows = await self._request("GET", "provider_models")
        return [ProviderModel.model_validate(r) for r in rows]
