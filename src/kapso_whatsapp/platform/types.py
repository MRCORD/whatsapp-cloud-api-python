"""
Pydantic models for the Kapso Platform API.

Each resource group appends its own models to this file under a clearly
labelled section. Shared envelope types (`PlatformMeta`, `PaginatedResponse`)
live at the top.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Envelope
# =============================================================================

T = TypeVar("T")


class PlatformMeta(BaseModel):
    """Pagination metadata returned by Platform list endpoints."""

    model_config = ConfigDict(extra="allow")

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1)
    total_pages: int = Field(default=1, ge=0)
    total_count: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Full Platform response envelope: data + pagination meta."""

    data: list[T]
    meta: PlatformMeta


# =============================================================================
# Customers
# =============================================================================


class Customer(BaseModel):
    """A customer record in your Kapso project."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    external_customer_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
