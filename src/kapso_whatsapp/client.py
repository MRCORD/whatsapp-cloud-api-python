"""
Kapso WhatsApp SDK Client

Main client for interacting with WhatsApp Business Cloud API.
Supports both direct Meta Graph API and Kapso proxy.

Provides:
- Connection pooling and retry logic
- Automatic authentication
- Resource-based API organization
- Type-safe requests and responses
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypeVar

import httpx

from .exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    WhatsAppAPIError,
    categorize_error,
)
from .types import ClientConfig

if TYPE_CHECKING:
    from .resources.calls import CallsResource
    from .resources.contacts import ContactsResource
    from .resources.conversations import ConversationsResource
    from .resources.flows import FlowsResource
    from .resources.media import MediaResource
    from .resources.messages import MessagesResource
    from .resources.phone_numbers import PhoneNumbersResource
    from .resources.templates import TemplatesResource

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_BASE_URL = "https://graph.facebook.com"
DEFAULT_GRAPH_VERSION = "v24.0"


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_snake_case_deep(obj: Any) -> Any:
    """Recursively convert dict keys from camelCase to snake_case."""
    if isinstance(obj, dict):
        return {_to_snake_case(k): _to_snake_case_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_snake_case_deep(item) for item in obj]
    return obj


class WhatsAppClient:
    """
    Minimal, async client for the WhatsApp Business Cloud API.

    Supports calling Meta Graph directly or via Kapso proxy.
    All resource helpers (messages, media, templates, etc.) hang off this client.

    Example:
        >>> client = WhatsAppClient(access_token="your_token")
        >>> await client.messages.send_text(
        ...     phone_number_id="123456",
        ...     to="+15551234567",
        ...     body="Hello from Kapso!"
        ... )
        >>> await client.close()

    Or use as context manager:
        >>> async with WhatsAppClient(access_token="your_token") as client:
        ...     await client.messages.send_text(...)
    """

    def __init__(
        self,
        *,
        access_token: str | None = None,
        kapso_api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        graph_version: str = DEFAULT_GRAPH_VERSION,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ) -> None:
        """
        Initialize WhatsApp client.

        Args:
            access_token: Meta access token for Graph API calls
            kapso_api_key: Kapso API key when using Kapso proxy
            base_url: Base URL (Meta Graph or Kapso proxy)
            graph_version: Graph API version (default: v23.0)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for retryable errors
            retry_backoff: Backoff multiplier for retries
        """
        if not access_token and not kapso_api_key:
            raise ValueError("Must provide either access_token or kapso_api_key")

        self._config = ClientConfig(
            access_token=access_token,
            kapso_api_key=kapso_api_key,
            base_url=base_url.rstrip("/"),
            graph_version=graph_version,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )

        self._client: httpx.AsyncClient | None = None
        self._closed = False

        # Lazy-loaded resources
        self._messages: MessagesResource | None = None
        self._media: MediaResource | None = None
        self._templates: TemplatesResource | None = None
        self._phone_numbers: PhoneNumbersResource | None = None
        self._flows: FlowsResource | None = None
        self._conversations: ConversationsResource | None = None
        self._contacts: ContactsResource | None = None
        self._calls: CallsResource | None = None

        logger.debug(f"Initialized WhatsAppClient with base_url={base_url}")

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def config(self) -> ClientConfig:
        """Get client configuration."""
        return self._config

    def is_kapso_proxy(self) -> bool:
        """Check if client is configured for Kapso proxy."""
        return "kapso.ai" in self._config.base_url

    # =========================================================================
    # Resource Properties (lazy-loaded)
    # =========================================================================

    @property
    def messages(self) -> MessagesResource:
        """Messages resource for sending messages."""
        if self._messages is None:
            from .resources.messages import MessagesResource
            self._messages = MessagesResource(self)
        return self._messages

    @property
    def media(self) -> MediaResource:
        """Media resource for uploading/downloading media."""
        if self._media is None:
            from .resources.media import MediaResource
            self._media = MediaResource(self)
        return self._media

    @property
    def templates(self) -> TemplatesResource:
        """Templates resource for managing message templates."""
        if self._templates is None:
            from .resources.templates import TemplatesResource
            self._templates = TemplatesResource(self)
        return self._templates

    @property
    def phone_numbers(self) -> PhoneNumbersResource:
        """Phone numbers resource for managing phone number settings."""
        if self._phone_numbers is None:
            from .resources.phone_numbers import PhoneNumbersResource
            self._phone_numbers = PhoneNumbersResource(self)
        return self._phone_numbers

    @property
    def flows(self) -> FlowsResource:
        """Flows resource for managing WhatsApp Flows."""
        if self._flows is None:
            from .resources.flows import FlowsResource
            self._flows = FlowsResource(self)
        return self._flows

    @property
    def conversations(self) -> ConversationsResource:
        """Conversations resource (Kapso proxy only)."""
        if self._conversations is None:
            from .resources.conversations import ConversationsResource
            self._conversations = ConversationsResource(self)
        return self._conversations

    @property
    def contacts(self) -> ContactsResource:
        """Contacts resource (Kapso proxy only)."""
        if self._contacts is None:
            from .resources.contacts import ContactsResource
            self._contacts = ContactsResource(self)
        return self._contacts

    @property
    def calls(self) -> CallsResource:
        """Calls resource (Kapso proxy only)."""
        if self._calls is None:
            from .resources.calls import CallsResource
            self._calls = CallsResource(self)
        return self._calls

    # =========================================================================
    # HTTP Client Management
    # =========================================================================

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": "Kapso-Python-SDK/0.1.0"}

            if self._config.access_token:
                headers["Authorization"] = f"Bearer {self._config.access_token}"

            if self._config.kapso_api_key:
                headers["X-API-Key"] = self._config.kapso_api_key

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._config.timeout),
                headers=headers,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
            logger.debug("Created new HTTP client with connection pooling")

        return self._client

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._closed = True
            logger.debug("Closed WhatsAppClient session")

    async def __aenter__(self) -> WhatsAppClient:
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()

    # =========================================================================
    # Request Methods
    # =========================================================================

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        clean_path = path.lstrip("/")
        return f"{self._config.base_url}/{self._config.graph_version}/{clean_path}"

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
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body (auto-serialized)
            data: Form data
            files: Files to upload
            headers: Additional headers

        Returns:
            Parsed JSON response

        Raises:
            WhatsAppAPIError: On API errors
            AuthenticationError: On auth errors
            RateLimitError: On rate limit errors
            NetworkError: On network errors
            TimeoutError: On timeout errors
        """
        client = await self._get_client()
        url = self._build_url(path)

        # Convert params to snake_case for API
        if params:
            params = _to_snake_case_deep(params)

        # Convert JSON body to snake_case for API
        if json:
            json = _to_snake_case_deep(json)

        retry_count = 0
        last_exception: WhatsAppAPIError | None = None

        while retry_count <= self._config.max_retries:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=headers,
                )

                logger.debug(
                    f"{method.upper()} {path} - Status: {response.status_code} - "
                    f"Attempt: {retry_count + 1}"
                )

                # Parse response
                try:
                    response_data: dict[str, Any] = response.json()
                except Exception:
                    response_data = {"text": response.text}

                # Success
                if response.status_code == 200:
                    return response_data

                # Handle errors
                error = categorize_error(response.status_code, response_data)

                # Handle rate limits with Retry-After header
                if isinstance(error, RateLimitError):
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        error.retry_after = int(retry_after)

                # Non-retryable errors
                if not error.is_retryable:
                    raise error

                last_exception = error

            except httpx.ConnectError as e:
                last_exception = NetworkError(f"Connection failed: {e}")
                logger.warning(f"Network error on attempt {retry_count + 1}: {e}")

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timeout: {e}")
                logger.warning(f"Timeout on attempt {retry_count + 1}")

            except (AuthenticationError, ValidationError):
                # Non-retryable errors - re-raise immediately
                raise

            # Check if we should retry
            if (
                last_exception
                and last_exception.is_retryable
                and retry_count < self._config.max_retries
            ):
                    retry_count += 1
                    wait_time = self._config.retry_backoff * (2 ** (retry_count - 1))

                    # Use Retry-After for rate limits
                    if isinstance(last_exception, RateLimitError) and last_exception.retry_after:
                        wait_time = last_exception.retry_after

                    logger.info(
                        f"Retrying in {wait_time:.1f}s "
                        f"(attempt {retry_count}/{self._config.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

            break

        # All retries exhausted
        if last_exception:
            logger.error(f"Request failed after {retry_count} retries: {last_exception}")
            raise last_exception

        raise WhatsAppAPIError("Request failed with unknown error")

    async def fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Fetch from absolute URL with client auth headers.

        Useful for downloading media from WhatsApp CDN URLs.

        Args:
            url: Absolute URL to fetch
            method: HTTP method
            headers: Additional headers
            **kwargs: Additional httpx request args

        Returns:
            Raw httpx Response
        """
        client = await self._get_client()
        return await client.request(method, url, headers=headers, **kwargs)

    async def raw_fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Fetch from URL without auth headers.

        Useful for public CDN URLs that reject Authorization headers.

        Args:
            url: Absolute URL to fetch
            method: HTTP method
            **kwargs: Additional httpx request args

        Returns:
            Raw httpx Response
        """
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, **kwargs)
