"""
KapsoPlatformClient — async client for the Kapso Platform API.

Sibling of `WhatsAppClient`. Both share `_HttpCore` for transport, retries,
and error mapping. This client owns Platform-specific concerns:

  * URL shape: `{base}/{path}` (no per-call version segment).
  * Auth: `X-API-Key` header only.
  * Response envelope: `{"data": ..., "meta": {...}}` — `request()` returns
    the unwrapped `data`; `request_raw()` returns the full envelope.
  * Pagination: page-based (`?page=N&per_page=N`); `paginate()` async
    generator iterates rows across pages.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from .._http import _HttpCore

if TYPE_CHECKING:
    from .resources.api_logs import ApiLogsResource
    from .resources.broadcasts import BroadcastsResource
    from .resources.contacts import ContactsResource
    from .resources.conversations import ConversationsResource
    from .resources.customers import CustomersResource
    from .resources.database import DatabaseResource
    from .resources.display_names import DisplayNamesResource
    from .resources.integrations import IntegrationsResource
    from .resources.media import MediaResource
    from .resources.messages import MessagesResource
    from .resources.phone_numbers import PhoneNumbersResource
    from .resources.project_webhooks import ProjectWebhooksResource
    from .resources.provider_models import ProviderModelsResource
    from .resources.setup_links import SetupLinksResource
    from .resources.users import UsersResource
    from .resources.webhook_deliveries import WebhookDeliveriesResource
    from .resources.webhooks import WebhooksResource
    from .resources.whatsapp_flows import WhatsAppFlowsResource

logger = logging.getLogger(__name__)

DEFAULT_PLATFORM_URL = "https://api.kapso.ai/platform/v1"


class KapsoPlatformClient:
    """
    Async client for the Kapso Platform API.

    Example:
        >>> async with KapsoPlatformClient(api_key="...") as kp:
        ...     customers = await kp.customers.list()
        ...     async for c in kp.customers.iter():
        ...         print(c.name)
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_PLATFORM_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http = _HttpCore(
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
            auth_headers={"X-API-Key": api_key},
        )
        self._closed = False

        # Lazy-loaded resources
        self._customers: CustomersResource | None = None
        self._broadcasts: BroadcastsResource | None = None
        self._provider_models: ProviderModelsResource | None = None
        self._messages: MessagesResource | None = None
        self._conversations: ConversationsResource | None = None
        self._contacts: ContactsResource | None = None
        self._media: MediaResource | None = None
        self._setup_links: SetupLinksResource | None = None
        self._phone_numbers: PhoneNumbersResource | None = None
        self._display_names: DisplayNamesResource | None = None
        self._users: UsersResource | None = None
        self._database: DatabaseResource | None = None
        self._integrations: IntegrationsResource | None = None
        self._api_logs: ApiLogsResource | None = None
        self._project_webhooks: ProjectWebhooksResource | None = None
        self._webhooks: WebhooksResource | None = None
        self._webhook_deliveries: WebhookDeliveriesResource | None = None
        self._whatsapp_flows: WhatsAppFlowsResource | None = None

        logger.debug("Initialized KapsoPlatformClient base_url=%s", self._base_url)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def base_url(self) -> str:
        return self._base_url

    # =========================================================================
    # Resource Properties (lazy-loaded)
    # =========================================================================

    @property
    def customers(self) -> CustomersResource:
        if self._customers is None:
            from .resources.customers import CustomersResource
            self._customers = CustomersResource(self)
        return self._customers

    @property
    def broadcasts(self) -> BroadcastsResource:
        if self._broadcasts is None:
            from .resources.broadcasts import BroadcastsResource
            self._broadcasts = BroadcastsResource(self)
        return self._broadcasts

    @property
    def provider_models(self) -> ProviderModelsResource:
        if self._provider_models is None:
            from .resources.provider_models import ProviderModelsResource
            self._provider_models = ProviderModelsResource(self)
        return self._provider_models

    @property
    def messages(self) -> MessagesResource:
        if self._messages is None:
            from .resources.messages import MessagesResource
            self._messages = MessagesResource(self)
        return self._messages

    @property
    def conversations(self) -> ConversationsResource:
        if self._conversations is None:
            from .resources.conversations import ConversationsResource
            self._conversations = ConversationsResource(self)
        return self._conversations

    @property
    def contacts(self) -> ContactsResource:
        if self._contacts is None:
            from .resources.contacts import ContactsResource
            self._contacts = ContactsResource(self)
        return self._contacts

    @property
    def media(self) -> MediaResource:
        if self._media is None:
            from .resources.media import MediaResource
            self._media = MediaResource(self)
        return self._media

    @property
    def database(self) -> DatabaseResource:
        if self._database is None:
            from .resources.database import DatabaseResource
            self._database = DatabaseResource(self)
        return self._database

    @property
    def integrations(self) -> IntegrationsResource:
        if self._integrations is None:
            from .resources.integrations import IntegrationsResource
            self._integrations = IntegrationsResource(self)
        return self._integrations

    @property
    def setup_links(self) -> SetupLinksResource:
        if self._setup_links is None:
            from .resources.setup_links import SetupLinksResource
            self._setup_links = SetupLinksResource(self)
        return self._setup_links

    @property
    def phone_numbers(self) -> PhoneNumbersResource:
        if self._phone_numbers is None:
            from .resources.phone_numbers import PhoneNumbersResource
            self._phone_numbers = PhoneNumbersResource(self)
        return self._phone_numbers

    @property
    def display_names(self) -> DisplayNamesResource:
        if self._display_names is None:
            from .resources.display_names import DisplayNamesResource
            self._display_names = DisplayNamesResource(self)
        return self._display_names

    @property
    def users(self) -> UsersResource:
        if self._users is None:
            from .resources.users import UsersResource
            self._users = UsersResource(self)
        return self._users

    @property
    def api_logs(self) -> ApiLogsResource:
        if self._api_logs is None:
            from .resources.api_logs import ApiLogsResource
            self._api_logs = ApiLogsResource(self)
        return self._api_logs

    @property
    def project_webhooks(self) -> ProjectWebhooksResource:
        if self._project_webhooks is None:
            from .resources.project_webhooks import ProjectWebhooksResource
            self._project_webhooks = ProjectWebhooksResource(self)
        return self._project_webhooks

    @property
    def webhooks(self) -> WebhooksResource:
        if self._webhooks is None:
            from .resources.webhooks import WebhooksResource
            self._webhooks = WebhooksResource(self)
        return self._webhooks

    @property
    def webhook_deliveries(self) -> WebhookDeliveriesResource:
        if self._webhook_deliveries is None:
            from .resources.webhook_deliveries import WebhookDeliveriesResource
            self._webhook_deliveries = WebhookDeliveriesResource(self)
        return self._webhook_deliveries

    @property
    def whatsapp_flows(self) -> WhatsAppFlowsResource:
        if self._whatsapp_flows is None:
            from .resources.whatsapp_flows import WhatsAppFlowsResource
            self._whatsapp_flows = WhatsAppFlowsResource(self)
        return self._whatsapp_flows

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def close(self) -> None:
        await self._http.close()
        self._closed = True

    async def __aenter__(self) -> KapsoPlatformClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    # =========================================================================
    # Request methods
    # =========================================================================

    def _build_url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make a Platform API request and return the full envelope (`data` + `meta`).

        Use this when you need pagination metadata or non-data fields. For most
        callers, prefer `request()` which returns the unwrapped `data` payload.
        """
        url = self._build_url(path)
        return await self._http.request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Make a Platform API request and return the unwrapped `data` payload.

        For paginated list endpoints `data` is a list; for single-resource
        endpoints it is an object. Endpoints that don't return a body
        (e.g. DELETE returning 204) yield an empty dict.
        """
        body = await self.request_raw(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
        if not isinstance(body, dict):
            return body
        if "data" in body:
            return body["data"]
        return body

    async def paginate(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        per_page: int = 20,
        start_page: int = 1,
        max_pages: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Iterate every row of a paginated list endpoint, advancing pages
        until `meta.page >= meta.total_pages`.

        Args:
            path: Endpoint path (e.g. "customers")
            params: Query string filters (excluding page/per_page)
            per_page: Page size
            start_page: First page to fetch
            max_pages: Optional hard cap on pages fetched (defensive)

        Yields:
            Each row as the raw dict the API returned. Resource helpers
            wrap these into Pydantic models.
        """
        page = start_page
        pages_fetched = 0
        while True:
            page_params: dict[str, Any] = dict(params or {})
            page_params["page"] = page
            page_params["per_page"] = per_page

            envelope = await self.request_raw("GET", path, params=page_params)
            rows = envelope.get("data") or []
            for row in rows:
                yield row

            meta = envelope.get("meta") or {}
            total_pages = int(meta.get("total_pages", 1))
            # Some Platform endpoints use `current_page` instead of `page` in
            # the meta envelope (e.g. display_names) — accept either.
            current_page = int(meta.get("page") or meta.get("current_page") or page)
            pages_fetched += 1

            if current_page >= total_pages:
                return
            if max_pages is not None and pages_fetched >= max_pages:
                return

            page = current_page + 1
