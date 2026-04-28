"""
Database resource for the Kapso Platform API.

Provides a PostgREST-style interface over project database tables.

Endpoints documented at:
  https://docs.kapso.ai/api/platform/v1/database/*

URL pattern: /db/{table} (note: "db", not "database")

Filter operators (passed as query params, PostgREST-style):
  column=eq.value      → WHERE column = value
  column=gt.value      → WHERE column > value
  column=gte.value     → WHERE column >= value
  column=lt.value      → WHERE column < value
  column=lte.value     → WHERE column <= value
  column=like.%value%  → WHERE column LIKE '%value%'
  column=in.(a,b,c)    → WHERE column IN (a, b, c)
  column=is.null       → WHERE column IS NULL
"""

from __future__ import annotations

from typing import Any

from .base import PlatformBaseResource


class DatabaseResource(PlatformBaseResource):
    """Interact with database tables on your Kapso project."""

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def query(
        self,
        table: str,
        *,
        select: str | None = None,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        **filters: str,
    ) -> list[dict[str, Any]]:
        """
        Query rows from a table (GET /db/{table}).

        Args:
            table:   Table name.
            select:  Comma-separated column list (e.g. "id,name,email").
            order:   Sort expression (e.g. "created_at.desc").
            limit:   Maximum rows to return (default 100).
            offset:  Number of rows to skip (default 0).
            **filters: PostgREST-style filter params, e.g. status="eq.active".

        Returns:
            List of row dicts.
        """
        params: dict[str, Any] = _filters(
            select=select,
            order=order,
            limit=limit,
            offset=offset,
            **filters,
        )
        rows = await self._request("GET", f"db/{table}", params=params)
        if isinstance(rows, list):
            return rows
        return []

    # ------------------------------------------------------------------
    # Get single row
    # ------------------------------------------------------------------

    async def get(self, table: str, row_id: str) -> dict[str, Any]:
        """
        Get a single row by ID (GET /db/{table}/{id}).

        Args:
            table:   Table name.
            row_id:  Row ID (string representation, e.g. "1" or a UUID).

        Returns:
            Row dict.
        """
        row = await self._request("GET", f"db/{table}/{row_id}")
        if isinstance(row, dict):
            return row
        return {}

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    async def insert(
        self,
        table: str,
        rows: dict[str, Any] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Insert one or more rows (POST /db/{table}).

        Args:
            table: Table name.
            rows:  Single row dict or list of row dicts.

        Returns:
            List of inserted rows as returned by the API.
        """
        result = await self._request("POST", f"db/{table}", json=rows)
        if isinstance(result, list):
            return result
        return []

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    async def upsert(
        self,
        table: str,
        rows: dict[str, Any] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Insert or update rows based on conflict key (PUT /db/{table}).

        Args:
            table: Table name.
            rows:  Single row dict or list of row dicts.

        Returns:
            List of upserted rows as returned by the API.
        """
        result = await self._request("PUT", f"db/{table}", json=rows)
        if isinstance(result, list):
            return result
        return []

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(
        self,
        table: str,
        fields: dict[str, Any],
        **filters: str,
    ) -> list[dict[str, Any]]:
        """
        Update rows matching filter criteria (PATCH /db/{table}).

        Filters are passed as PostgREST-style query params:
          e.g. status="eq.active"

        Args:
            table:    Table name.
            fields:   Dict of column → new value pairs.
            **filters: PostgREST-style filter params for WHERE clause.

        Returns:
            List of updated rows as returned by the API.
        """
        params: dict[str, Any] = _filters(**filters)
        result = await self._request(
            "PATCH",
            f"db/{table}",
            params=params or None,
            json=fields,
        )
        if isinstance(result, list):
            return result
        return []

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(
        self,
        table: str,
        **filters: str,
    ) -> None:
        """
        Delete rows matching filter criteria (DELETE /db/{table}).

        Filters are passed as PostgREST-style query params:
          e.g. status="eq.inactive"

        Args:
            table:     Table name.
            **filters: PostgREST-style filter params for WHERE clause.
        """
        params: dict[str, Any] = _filters(**filters)
        await self._request("DELETE", f"db/{table}", params=params or None)


def _filters(**kwargs: Any) -> dict[str, Any]:
    """Drop keys whose value is None — let API defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}
