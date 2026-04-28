"""
Read-only smoke test for KapsoPlatformClient against the live API.

Hits one or two GET endpoints from each resource group to confirm response
shape matches what the SDK expects. Does NOT create, modify, or delete any
data. Run:

    KAPSO_API_TOKEN=… python examples/platform_smoke.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback

from kapso_whatsapp import KapsoPlatformClient


async def _try(label: str, factory):  # type: ignore[no-untyped-def]
    """factory is a zero-arg callable returning a coroutine — so a TypeError
    raised at coroutine construction is caught here too."""
    try:
        result = await factory()
        n = len(result) if hasattr(result, "__len__") else "?"
        print(f"  ✓ {label}: {n} items / {type(result).__name__}")
        return result
    except Exception as e:  # noqa: BLE001 — smoke script wants every failure
        print(f"  ✗ {label}: {type(e).__name__}: {e}")
        return None


async def main() -> int:
    api_key = os.environ.get("KAPSO_PLATFORM_API_KEY") or os.environ.get("KAPSO_API_TOKEN")
    if not api_key:
        print("error: set KAPSO_PLATFORM_API_KEY or KAPSO_API_TOKEN", file=sys.stderr)
        return 1

    print(f"smoke against api.kapso.ai/platform/v1 with key …{api_key[-4:]}\n")

    async with KapsoPlatformClient(api_key=api_key) as kp:
        print("== Customers ==")
        customers = await _try("customers.list(per_page=5)", lambda: kp.customers.list(per_page=5))
        first_customer_id = customers[0].id if customers else None

        print("\n== Setup links ==")
        if first_customer_id:
            await _try(
                "setup_links.list(customer_id=…)",
                lambda: kp.setup_links.list(customer_id=first_customer_id, per_page=5),
            )
        else:
            print("  - skipped (no customer_id available)")

        print("\n== Phone numbers ==")
        phones = await _try("phone_numbers.list()", lambda: kp.phone_numbers.list())
        first_phone_id = phones[0].id if phones else None

        print("\n== Display names ==")
        if first_phone_id:
            await _try(
                "display_names.list(phone_number_id=…)",
                lambda: kp.display_names.list(phone_number_id=first_phone_id),
            )
        else:
            print("  - skipped (no phone_number_id available)")

        print("\n== Users ==")
        await _try("users.list()", lambda: kp.users.list())

        print("\n== Broadcasts ==")
        await _try("broadcasts.list(per_page=5)", lambda: kp.broadcasts.list(per_page=5))

        print("\n== Messages ==")
        await _try("messages.list(per_page=5)", lambda: kp.messages.list(per_page=5))

        print("\n== Conversations ==")
        await _try("conversations.list(per_page=5)", lambda: kp.conversations.list(per_page=5))

        print("\n== Contacts ==")
        await _try("contacts.list(per_page=5)", lambda: kp.contacts.list(per_page=5))

        print("\n== Project webhooks ==")
        await _try("project_webhooks.list()", lambda: kp.project_webhooks.list())

        print("\n== Webhooks ==")
        if first_phone_id:
            await _try(
                "webhooks.list(phone_number_id=…)",
                lambda: kp.webhooks.list(phone_number_id=first_phone_id),
            )
        else:
            print("  - skipped (no phone_number_id available)")

        print("\n== Webhook deliveries ==")
        await _try("webhook_deliveries.list(per_page=5)", lambda: kp.webhook_deliveries.list(per_page=5))

        print("\n== API logs ==")
        await _try("api_logs.list(per_page=5)", lambda: kp.api_logs.list(per_page=5))

        print("\n== Provider models ==")
        await _try("provider_models.list()", lambda: kp.provider_models.list())

        print("\n== Integrations ==")
        await _try("integrations.list()", lambda: kp.integrations.list())

        print("\n== WhatsApp Flows ==")
        await _try("whatsapp_flows.list(per_page=5)", lambda: kp.whatsapp_flows.list(per_page=5))

    print("\ndone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
