"""
Shared async HTTP transport for kapso_whatsapp clients.

Provides connection pooling, retry-with-backoff, and error categorization.
Both WhatsAppClient and KapsoPlatformClient delegate their network plumbing
here so retry/auth/error-handling logic lives in one place.

This module is internal — public callers go through WhatsAppClient or
KapsoPlatformClient.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

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

logger = logging.getLogger(__name__)


class _HttpCore:
    """
    Internal async HTTP core: pool, retries, error mapping.

    Owned by a public client (WhatsAppClient / KapsoPlatformClient). Callers
    pass already-built absolute URLs; URL construction and request-shape
    conventions belong to the owning client.
    """

    def __init__(
        self,
        *,
        timeout: float,
        max_retries: int,
        retry_backoff: float,
        auth_headers: dict[str, str],
        user_agent: str = "Kapso-Python-SDK/0.2.0",
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._headers = {"User-Agent": user_agent, **auth_headers}
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create pooled httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers=self._headers,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
            logger.debug("Created new HTTP client with connection pooling")
        return self._client

    async def close(self) -> None:
        """Close pooled client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("Closed HTTP core session")

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute HTTP request with retry-on-retryable-error.

        Args:
            method: HTTP method
            url: Absolute URL (caller is responsible for building it)
            params: Query string params
            json: JSON body (already in target case — no conversion here)
            data: Form data
            files: Multipart files
            headers: Extra per-request headers

        Returns:
            Parsed JSON response body. Falls back to {"text": <body>} for
            non-JSON responses.

        Raises:
            WhatsAppAPIError (or subclass) on non-2xx after retries are exhausted.
        """
        client = await self.get_client()

        retry_count = 0
        last_exception: WhatsAppAPIError | None = None

        while retry_count <= self._max_retries:
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
                    "%s %s - status=%s attempt=%s",
                    method.upper(),
                    url,
                    response.status_code,
                    retry_count + 1,
                )

                try:
                    response_data: dict[str, Any] = response.json()
                except (ValueError, TypeError):
                    response_data = {"text": response.text}

                if 200 <= response.status_code < 300:
                    return response_data

                error = categorize_error(response.status_code, response_data)

                if isinstance(error, RateLimitError):
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        with contextlib.suppress(ValueError):
                            error.retry_after = int(retry_after)

                if not error.is_retryable:
                    raise error

                last_exception = error

            except httpx.ConnectError as e:
                last_exception = NetworkError(f"Connection failed: {e}")
                logger.warning("Network error on attempt %s: %s", retry_count + 1, e)

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timeout: {e}")
                logger.warning("Timeout on attempt %s", retry_count + 1)

            except (AuthenticationError, ValidationError):
                raise

            if (
                last_exception
                and last_exception.is_retryable
                and retry_count < self._max_retries
            ):
                retry_count += 1
                wait_time = self._retry_backoff * (2 ** (retry_count - 1))

                if isinstance(last_exception, RateLimitError) and last_exception.retry_after:
                    wait_time = float(last_exception.retry_after)

                logger.info(
                    "Retrying in %.1fs (attempt %s/%s)",
                    wait_time,
                    retry_count,
                    self._max_retries,
                )
                await asyncio.sleep(wait_time)
                continue

            break

        if last_exception:
            logger.error("Request failed after %s retries: %s", retry_count, last_exception)
            raise last_exception

        raise WhatsAppAPIError("Request failed with unknown error")
