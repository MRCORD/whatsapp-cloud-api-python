"""Tests for webhook utilities."""

from __future__ import annotations

import hashlib
import hmac
import json

from kapso_whatsapp.webhooks import (
    NormalizedWebhookResult,
    normalize_webhook,
    verify_signature,
)


class TestVerifySignature:
    """Test signature verification."""

    def test_valid_signature(self) -> None:
        """Should return True for valid signature."""
        app_secret = "test_secret_12345"
        raw_body = b'{"test": "data"}'

        # Compute expected signature
        expected_sig = hmac.new(
            app_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        result = verify_signature(
            app_secret=app_secret,
            raw_body=raw_body,
            signature_header=f"sha256={expected_sig}",
        )
        assert result is True

    def test_invalid_signature(self) -> None:
        """Should return False for invalid signature."""
        result = verify_signature(
            app_secret="real_secret",
            raw_body=b'{"test": "data"}',
            signature_header="sha256=0000000000000000000000000000000000000000000000000000000000000000",
        )
        assert result is False

    def test_missing_signature(self) -> None:
        """Should return False for missing signature."""
        result = verify_signature(
            app_secret="secret",
            raw_body=b"body",
            signature_header=None,
        )
        assert result is False

    def test_malformed_signature(self) -> None:
        """Should return False for malformed signature header."""
        result = verify_signature(
            app_secret="secret",
            raw_body=b"body",
            signature_header="invalid_format",
        )
        assert result is False

    def test_wrong_algorithm(self) -> None:
        """Should return False for wrong algorithm."""
        result = verify_signature(
            app_secret="secret",
            raw_body=b"body",
            signature_header="sha512=abc123",
        )
        assert result is False

    def test_string_body(self) -> None:
        """Should handle string body."""
        app_secret = "test_secret"
        raw_body = '{"test": "data"}'

        expected_sig = hmac.new(
            app_secret.encode(),
            raw_body.encode(),
            hashlib.sha256,
        ).hexdigest()

        result = verify_signature(
            app_secret=app_secret,
            raw_body=raw_body,
            signature_header=f"sha256={expected_sig}",
        )
        assert result is True


class TestNormalizeWebhook:
    """Test webhook normalization."""

    def test_empty_payload(self) -> None:
        """Should handle empty payload."""
        result = normalize_webhook(None)
        assert isinstance(result, NormalizedWebhookResult)
        assert result.messages == []
        assert result.statuses == []

    def test_message_extraction(self) -> None:
        """Should extract messages from payload."""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123",
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": "111222333",
                                    "display_phone_number": "15551234567",
                                },
                                "messages": [
                                    {
                                        "id": "wamid.abc123",
                                        "from": "15559876543",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello!"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        result = normalize_webhook(payload)

        assert result.object == "whatsapp_business_account"
        assert result.phone_number_id == "111222333"
        assert len(result.messages) == 1
        assert result.messages[0]["id"] == "wamid.abc123"
        assert result.messages[0]["text"]["body"] == "Hello!"

    def test_status_extraction(self) -> None:
        """Should extract statuses from payload."""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": "wamid.xyz789",
                                        "status": "delivered",
                                        "timestamp": "1234567890",
                                        "recipient_id": "15559876543",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        result = normalize_webhook(payload)

        assert len(result.statuses) == 1
        assert result.statuses[0].id == "wamid.xyz789"
        assert result.statuses[0].status == "delivered"
        assert result.statuses[0].recipient_id == "15559876543"

    def test_camel_case_conversion(self) -> None:
        """Should convert snake_case to camelCase."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123"},
                                "messages": [
                                    {
                                        "id": "msg1",
                                        "from": "456",
                                        "message_status": "sent",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        result = normalize_webhook(payload)

        assert len(result.messages) == 1
        assert "messageStatus" in result.messages[0]

    def test_direction_inference_inbound(self) -> None:
        """Should infer inbound direction for messages from external numbers."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "business123"},
                                "messages": [
                                    {"id": "msg1", "from": "customer456"}
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        result = normalize_webhook(payload)

        assert len(result.messages) == 1
        assert result.messages[0].get("kapso", {}).get("direction") == "inbound"

    def test_json_string_payload(self) -> None:
        """Should handle JSON string payload."""
        payload = json.dumps(
            {
                "object": "whatsapp_business_account",
                "entry": [{"changes": [{"value": {}, "field": "messages"}]}],
            }
        )

        result = normalize_webhook(payload)
        assert result.object == "whatsapp_business_account"
