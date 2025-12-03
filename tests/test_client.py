"""Tests for WhatsAppClient."""

from __future__ import annotations

import pytest

from kapso_whatsapp import WhatsAppClient


class TestClientInitialization:
    """Test client initialization."""

    def test_requires_auth(self) -> None:
        """Should require either access_token or kapso_api_key."""
        with pytest.raises(ValueError, match="Must provide either"):
            WhatsAppClient()

    def test_accepts_access_token(self, access_token: str) -> None:
        """Should accept access_token."""
        client = WhatsAppClient(access_token=access_token)
        assert client.config.access_token == access_token
        assert client.config.kapso_api_key is None

    def test_accepts_kapso_api_key(self, kapso_api_key: str) -> None:
        """Should accept kapso_api_key."""
        client = WhatsAppClient(
            kapso_api_key=kapso_api_key, base_url="https://api.kapso.ai"
        )
        assert client.config.kapso_api_key == kapso_api_key
        assert client.config.access_token is None

    def test_default_config(self, access_token: str) -> None:
        """Should use default configuration values."""
        client = WhatsAppClient(access_token=access_token)
        assert client.config.base_url == "https://graph.facebook.com"
        assert client.config.graph_version == "v24.0"
        assert client.config.timeout == 30.0
        assert client.config.max_retries == 3

    def test_custom_config(self, access_token: str) -> None:
        """Should accept custom configuration."""
        client = WhatsAppClient(
            access_token=access_token,
            base_url="https://custom.api.com",
            graph_version="v22.0",
            timeout=60.0,
            max_retries=5,
        )
        assert client.config.base_url == "https://custom.api.com"
        assert client.config.graph_version == "v22.0"
        assert client.config.timeout == 60.0
        assert client.config.max_retries == 5


class TestClientResources:
    """Test resource property access."""

    def test_messages_resource(self, access_token: str) -> None:
        """Should provide messages resource."""
        client = WhatsAppClient(access_token=access_token)
        messages = client.messages
        assert messages is not None
        # Verify lazy loading - same instance on second access
        assert client.messages is messages

    def test_media_resource(self, access_token: str) -> None:
        """Should provide media resource."""
        client = WhatsAppClient(access_token=access_token)
        media = client.media
        assert media is not None
        assert client.media is media

    def test_templates_resource(self, access_token: str) -> None:
        """Should provide templates resource."""
        client = WhatsAppClient(access_token=access_token)
        templates = client.templates
        assert templates is not None
        assert client.templates is templates

    def test_flows_resource(self, access_token: str) -> None:
        """Should provide flows resource."""
        client = WhatsAppClient(access_token=access_token)
        flows = client.flows
        assert flows is not None
        assert client.flows is flows


class TestKapsoProxyDetection:
    """Test Kapso proxy detection."""

    def test_detects_kapso_proxy(self, kapso_api_key: str) -> None:
        """Should detect Kapso proxy URL."""
        client = WhatsAppClient(
            kapso_api_key=kapso_api_key,
            base_url="https://api.kapso.ai",
        )
        assert client.is_kapso_proxy()

    def test_detects_meta_graph(self, access_token: str) -> None:
        """Should detect Meta Graph URL."""
        client = WhatsAppClient(access_token=access_token)
        assert not client.is_kapso_proxy()


class TestClientContextManager:
    """Test async context manager."""

    async def test_context_manager(self, access_token: str) -> None:
        """Should work as async context manager."""
        async with WhatsAppClient(access_token=access_token) as client:
            assert client is not None
            # Force client creation by making a request attribute access
            _ = client.config

        # After context, client should be marked as closed
        # Note: _closed is set after close() is called
        assert client._closed or client._client is None or client._client.is_closed
