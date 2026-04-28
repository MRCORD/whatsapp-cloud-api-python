"""
Customers resource for the Kapso Platform API.

Reference template — Phase 2 sub-agents copy this pattern for the other 17
resources. Keep the public method shapes consistent across resources:

  * `list(...)` — fetch one page (returns list[Model])
  * `iter(...)` — async generator across all pages (yields Model)
  * `get(<id>)` — single resource by id
  * `create(...)` — create
  * `update(<id>, ...)` — partial update
  * `delete(<id>)` — delete

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/customers/*
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..types import Customer
from .base import PlatformBaseResource


class CustomersResource(PlatformBaseResource):
    """Manage customers on your Kapso project."""

    async def list(
        self,
        *,
        name_contains: str | None = None,
        external_customer_id: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Customer]:
        """List customers (single page). For full-iteration use `iter()`."""
        params = _filters(
            name_contains=name_contains,
            external_customer_id=external_customer_id,
            created_after=created_after,
            created_before=created_before,
            per_page=per_page,
            page=page,
        )
        rows = await self._request("GET", "customers", params=params)
        return [Customer.model_validate(r) for r in rows]

    async def iter(
        self,
        *,
        name_contains: str | None = None,
        external_customer_id: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        per_page: int = 20,
    ) -> AsyncIterator[Customer]:
        """Async iterator over every customer matching the filters."""
        params = _filters(
            name_contains=name_contains,
            external_customer_id=external_customer_id,
            created_after=created_after,
            created_before=created_before,
        )
        async for row in self._client.paginate("customers", params=params, per_page=per_page):
            yield Customer.model_validate(row)

    async def get(self, customer_id: str) -> Customer:
        """Fetch a single customer by id."""
        row = await self._request("GET", f"customers/{customer_id}")
        return Customer.model_validate(row)

    async def create(
        self,
        *,
        name: str,
        external_customer_id: str | None = None,
    ) -> Customer:
        """Create a new customer."""
        payload: dict[str, Any] = {"name": name}
        if external_customer_id is not None:
            payload["external_customer_id"] = external_customer_id
        row = await self._request("POST", "customers", json={"customer": payload})
        return Customer.model_validate(row)

    async def update(
        self,
        customer_id: str,
        *,
        name: str | None = None,
        external_customer_id: str | None = None,
    ) -> Customer:
        """Partial update — only fields you pass are sent."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if external_customer_id is not None:
            payload["external_customer_id"] = external_customer_id
        row = await self._request(
            "PATCH",
            f"customers/{customer_id}",
            json={"customer": payload},
        )
        return Customer.model_validate(row)

    async def delete(self, customer_id: str) -> None:
        """Delete a customer."""
        await self._request("DELETE", f"customers/{customer_id}")


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
