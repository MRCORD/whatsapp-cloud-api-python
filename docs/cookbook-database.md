# Kapso Database Cookbook

`kp.database` exposes a PostgREST-style interface over project-scoped database tables. It is for application state you control — not a replacement for your primary datastore, and not queryable across projects. For endpoint details see [platform-api.md](./platform-api.md#database).

---

## 1. Quick Start

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        # Write a row
        await kp.database.insert("leads", {"id": "lead-1", "name": "Alice", "status": "new"})

        # Read it back
        rows = await kp.database.query("leads", status="eq.new")
        print(rows)

asyncio.run(main())
```

Filters are PostgREST operators passed as keyword arguments: `column="op.value"`. The table is created automatically on first write.

---

## 2. Idempotent Upsert

Sync external records into Kapso DB without creating duplicates on repeated runs.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

# Simulated CRM payload — could arrive from a webhook or nightly job
CRM_CUSTOMERS = [
    {"id": "crm-001", "name": "Acme Corp",    "tier": "enterprise", "phone": "+15551110001"},
    {"id": "crm-002", "name": "Globex LLC",   "tier": "starter",    "phone": "+15551110002"},
    {"id": "crm-003", "name": "Initech Ltd",  "tier": "enterprise", "phone": "+15551110003"},
]

async def sync_crm_customers(kp: KapsoPlatformClient) -> None:
    result = await kp.database.upsert("customers", CRM_CUSTOMERS)
    print(f"upserted {len(result)} rows")

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        # Safe to call multiple times — existing rows are updated, new rows inserted
        await sync_crm_customers(kp)
        await sync_crm_customers(kp)  # second call does not duplicate

asyncio.run(main())
```

`upsert()` issues a PUT to `/db/{table}`. The API resolves conflicts on the row's primary key (`id`). Pass a list for bulk sync or a single dict for one record. The returned list contains the final state of every affected row.

---

## 3. Query Composition

Build multi-condition queries with ordering and column projection.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:

        # Single condition
        new_leads = await kp.database.query("leads", status="eq.new")

        # Multiple conditions (AND semantics — all kwargs must match)
        enterprise_leads = await kp.database.query(
            "leads",
            status="eq.qualified",
            tier="eq.enterprise",
        )

        # Range filter + ordering + column projection
        recent_events = await kp.database.query(
            "events",
            select="id,contact_id,type,occurred_at",
            occurred_at="gte.2026-01-01T00:00:00Z",
            order="occurred_at.desc",
            limit=50,
        )

        # NULL check — contacts with no assigned owner
        unassigned = await kp.database.query("leads", owner_id="is.null")

        # IN list — fetch a known set of records
        specific = await kp.database.query(
            "customers",
            tier="in.(enterprise,growth)",
        )

        # LIKE pattern — name starts with "Ac"
        named = await kp.database.query("customers", name="like.Ac%")

asyncio.run(main())
```

All filter kwargs become PostgREST query parameters. Multiple kwargs are ANDed. `order` takes `column.asc` or `column.desc`. `select` is a comma-separated column list; omit it to receive all columns. Missing keys in stored rows come back as `None` — they do not raise an error.

**Supported operators:**

| Suffix | SQL equivalent |
|---|---|
| `eq.value` | `= value` |
| `gt.value` | `> value` |
| `gte.value` | `>= value` |
| `lt.value` | `< value` |
| `lte.value` | `<= value` |
| `like.%val%` | `LIKE '%val%'` |
| `in.(a,b,c)` | `IN (a, b, c)` |
| `is.null` | `IS NULL` |

---

## 4. Pagination Patterns

`query()` is not auto-paginating. Walk pages manually using `offset`.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

PAGE_SIZE = 100

async def iter_all_leads(kp: KapsoPlatformClient):
    """Yield every row from 'leads' one page at a time."""
    offset = 0
    while True:
        page = await kp.database.query(
            "leads",
            order="id.asc",   # stable ordering is required for correct pagination
            limit=PAGE_SIZE,
            offset=offset,
        )
        if not page:
            break
        for row in page:
            yield row
        if len(page) < PAGE_SIZE:
            break          # last page was partial — no further request needed
        offset += PAGE_SIZE

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        count = 0
        async for lead in iter_all_leads(kp):
            count += 1
        print(f"total leads: {count}")

asyncio.run(main())
```

**Fetch everything at once — only when safe:**

```python
async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        # Fine for small tables (< a few thousand rows).
        # Do not use on large or unbounded tables — the response payload and
        # memory usage grow linearly with row count.
        all_rows = await kp.database.query("customers", limit=10_000)
asyncio.run(main())
```

`query()` enforces a server-side maximum. If you exceed it the API silently caps the result — it does not error. Always check `len(page) < PAGE_SIZE` rather than assuming a short page means end-of-data only when the limit is exactly `PAGE_SIZE`. Use `order` on a stable unique column (`id` or `created_at`) so pages are consistent across calls.

---

## 5. Schema-Light Migrations

The Kapso DB is schema-flexible: adding or renaming columns is done by reading and rewriting rows.

**Example: split a `full_name` column into `first_name` and `last_name`.**

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

PAGE_SIZE = 100

async def migrate_name_split(kp: KapsoPlatformClient) -> None:
    """
    For every contact row that has full_name but no first_name,
    split the value and write the new columns back.
    """
    offset = 0
    migrated = 0

    while True:
        # Fetch rows that still need migration
        rows = await kp.database.query(
            "contacts",
            full_name="not.is.null",   # has a value to split
            first_name="is.null",      # not yet migrated
            select="id,full_name",
            order="id.asc",
            limit=PAGE_SIZE,
            offset=offset,
        )
        if not rows:
            break

        for row in rows:
            parts = (row.get("full_name") or "").split(" ", 1)
            first = parts[0]
            last  = parts[1] if len(parts) > 1 else ""

            await kp.database.update(
                "contacts",
                {"first_name": first, "last_name": last},
                id=f"eq.{row['id']}",
            )
            migrated += 1

        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"migrated {migrated} rows")

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        await migrate_name_split(kp)

asyncio.run(main())
```

`update(table, fields, **filters)` takes a dict of column-to-value pairs and PostgREST filter kwargs. It applies to every row matching the filters, so always include a precise filter (here `id="eq.{row['id']}"`) unless you intend a bulk update. The migration is safe to re-run: rows that already have `first_name` are excluded by the `first_name="is.null"` filter.

---

## 6. `get` vs `query(limit=1)`

Retrieve a row whose primary key you already know.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient
from kapso_whatsapp import NotFoundError

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:

        # --- get: primary-key lookup, O(1) ---
        # Use when you have the exact row ID.
        # Raises NotFoundError if the row does not exist.
        try:
            lead = await kp.database.get("leads", "lead-001")
            print(lead["name"])
        except NotFoundError:
            print("lead not found")

        # --- query(limit=1): arbitrary filter ---
        # Use when you are searching by a non-primary-key column.
        # Returns an empty list (not an exception) when no rows match.
        rows = await kp.database.query(
            "leads",
            email="eq.alice@example.com",
            limit=1,
        )
        if rows:
            print(rows[0]["name"])
        else:
            print("no match")

asyncio.run(main())
```

| | `get(table, row_id)` | `query(..., limit=1)` |
|---|---|---|
| Lookup by | Primary key | Any column(s) |
| Not-found behavior | Raises `NotFoundError` | Returns `[]` |
| Performance | Direct key lookup | Full filter scan |
| Use case | You have the ID | You have a non-key value |

Never use `query(limit=1)` as a substitute for `get` when you have the ID — it wastes a filter scan and loses the explicit not-found signal.

---

## 7. Error Patterns

Handle the errors `kp.database` can produce in production code.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient, NotFoundError, ValidationError

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:

        # --- NotFoundError: row does not exist ---
        try:
            row = await kp.database.get("leads", "nonexistent-id")
        except NotFoundError:
            # Safe to handle: create the row, return a default, or re-raise
            print("row not found")

        # --- ValidationError: malformed filter or bad type ---
        # Example: passing a non-string value as a filter operand.
        # The API returns 400/422 which the SDK raises as ValidationError.
        try:
            rows = await kp.database.query("leads", created_at="eq.not-a-date")
        except ValidationError as exc:
            print(f"bad filter: {exc}")

        # --- Silent type coercion ---
        # Numbers stored as strings are returned as strings.
        # There is no schema enforcement; always coerce after read.
        await kp.database.insert("events", {"contact_id": "c-1", "score": "42"})
        rows = await kp.database.query("events", contact_id="eq.c-1", limit=1)
        score = int(rows[0]["score"]) if rows else 0   # explicit cast required

        # --- Missing column — no error, value is None ---
        # Querying a column that was never written returns None in the row dict,
        # not a KeyError or a ValidationError.
        rows = await kp.database.query("leads", limit=1)
        owner = rows[0].get("owner_id")   # None if the column was never set
        print(f"owner: {owner!r}")

        # --- Bulk update without a filter — affects ALL rows ---
        # Forgetting a filter on update() updates every row in the table.
        # Always double-check that at least one filter kwarg is present.
        try:
            if not True:   # guard: never run unfiltered update in production
                await kp.database.update("leads", {"status": "archived"})
        except Exception:
            pass

        # --- delete() with no filters deletes the entire table ---
        # The API accepts a DELETE with no filters and removes all rows.
        # Protect destructive calls behind an explicit id filter.
        await kp.database.delete("leads", id="eq.lead-001")   # safe: one row
        # await kp.database.delete("leads")  # DANGER: drops all rows

asyncio.run(main())
```

Key points:

- `get()` raises `NotFoundError` on a missing row; `query()` returns `[]`.
- `ValidationError` covers 400 and 422 responses (malformed operators, type mismatches the API rejects).
- Silent coercion: the Kapso DB stores values as-is. A number written as a string comes back as a string. Cast explicitly after reading.
- Missing columns silently return `None` — use `.get("column")` instead of `["column"]`.
- `update()` and `delete()` with no filter kwargs affect the entire table. Always include at least one filter in production code.
