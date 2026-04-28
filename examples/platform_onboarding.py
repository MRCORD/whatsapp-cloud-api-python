"""
Onboard a customer end-to-end via the Kapso Platform API.

Run:
    KAPSO_PLATFORM_API_KEY=kp_live_… python examples/platform_onboarding.py
"""

from __future__ import annotations

import asyncio
import os

from kapso_whatsapp import KapsoPlatformClient


async def main() -> None:
    api_key = os.environ.get("KAPSO_PLATFORM_API_KEY") or os.environ["KAPSO_API_TOKEN"]

    async with KapsoPlatformClient(api_key=api_key) as kp:
        # 1. Create the customer record on your Kapso project.
        customer = await kp.customers.create(
            name="Acme Corp",
            external_customer_id="cus_acme_001",
        )
        print(f"created customer {customer.id} ({customer.name})")

        # 2. Generate a setup link they can use to connect their WhatsApp.
        setup = await kp.setup_links.create(customer_id=customer.id)
        print(f"send the customer this link: {setup.url}")

        # 3. List everyone you've onboarded so far (paginated, async).
        async for c in kp.customers.iter(per_page=50):
            print(f"  - {c.name} ({c.external_customer_id})")


if __name__ == "__main__":
    asyncio.run(main())
