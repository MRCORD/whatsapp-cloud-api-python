"""Pytest fixtures for kapso-whatsapp tests."""

from __future__ import annotations

from typing import Any

import pytest
import respx
from httpx import Response

from kapso_whatsapp import WhatsAppClient


@pytest.fixture
def access_token() -> str:
    """Sample access token for tests."""
    return "test_access_token_12345"


@pytest.fixture
def kapso_api_key() -> str:
    """Sample Kapso API key for tests."""
    return "test_kapso_api_key_12345"


@pytest.fixture
def phone_number_id() -> str:
    """Sample phone number ID."""
    return "123456789012345"


@pytest.fixture
def recipient_phone() -> str:
    """Sample recipient phone number."""
    return "+15551234567"


@pytest.fixture
def sample_message_response() -> dict[str, Any]:
    """Sample successful message response."""
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "+15551234567", "wa_id": "15551234567"}],
        "messages": [{"id": "wamid.abc123xyz456"}],
    }


@pytest.fixture
async def client(access_token: str) -> WhatsAppClient:
    """Create a WhatsApp client for testing."""
    return WhatsAppClient(access_token=access_token)


@pytest.fixture
async def kapso_client(kapso_api_key: str) -> WhatsAppClient:
    """Create a Kapso-configured client for testing."""
    return WhatsAppClient(
        kapso_api_key=kapso_api_key,
        base_url="https://api.kapso.ai",
    )


@pytest.fixture
def mock_api() -> respx.MockRouter:
    """Create a respx mock router."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def mock_send_text_success(
    mock_api: respx.MockRouter,
    sample_message_response: dict[str, Any],
    phone_number_id: str,
) -> respx.Route:
    """Mock successful text message send."""
    return mock_api.post(
        f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
    ).mock(return_value=Response(200, json=sample_message_response))
