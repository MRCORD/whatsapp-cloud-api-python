"""
Kapso Platform API client.

Manages your Kapso project itself (customers, setup links, broadcasts,
webhooks, database, integrations, WhatsApp Flow lifecycle, etc.) — separate
from the WhatsApp messaging API exposed by `WhatsAppClient`.

Example:
    >>> from kapso_whatsapp import KapsoPlatformClient
    >>> async with KapsoPlatformClient(api_key="...") as kp:
    ...     customers = await kp.customers.list()
"""

from .client import DEFAULT_PLATFORM_URL, KapsoPlatformClient
from .types import Customer, PlatformMeta

__all__ = [
    "KapsoPlatformClient",
    "DEFAULT_PLATFORM_URL",
    "PlatformMeta",
    "Customer",
]
