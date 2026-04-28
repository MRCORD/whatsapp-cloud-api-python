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


# =============================================================================
# BSUID compatibility (rolling out 2026)
# =============================================================================


class TestBsuidPayloads:
    """Verify the SDK handles business-scoped user ID payloads.

    See: https://docs.kapso.ai/docs/whatsapp/business-scoped-user-ids
    """

    @staticmethod
    def _wrap_messages(messages: list[dict]) -> dict:
        """Wrap a list of message dicts into a Meta-style webhook envelope."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": "111222333",
                                    "display_phone_number": "+15551234567",
                                },
                                "messages": messages,
                            },
                        }
                    ]
                }
            ],
        }

    @staticmethod
    def _wrap_value(value: dict, field_name: str = "messages") -> dict:
        """Wrap an arbitrary `value` dict into the webhook envelope."""
        return {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"field": field_name, "value": value}]}],
        }

    # -- WebhookMessage / normalize: BSUID-only inbound -------------------

    def test_bsuid_only_message_normalizes(self) -> None:
        payload = self._wrap_messages([
            {
                "id": "wamid.bsuid",
                "timestamp": "1700000000",
                "type": "text",
                "text": {"body": "hello from BSUID-only"},
                "business_scoped_user_id": "US.13491208655302741918",
                "username": "@testuser",
                # NOTE: no `from`, no `wa_id` — full BSUID-only path
            }
        ])
        result = normalize_webhook(payload)
        assert len(result.messages) == 1
        msg = result.messages[0]
        assert msg.get("businessScopedUserId") == "US.13491208655302741918"
        assert msg.get("username") == "@testuser"
        # Direction should still be inferred as inbound (Meta only routes BSUID-only
        # payloads user → business)
        assert msg["kapso"]["direction"] == "inbound"

    def test_bsuid_plus_phone_message_normalizes(self) -> None:
        """Transition window: both phone + BSUID present."""
        payload = self._wrap_messages([
            {
                "id": "wamid.both",
                "from": "16315551181",
                "timestamp": "1700000001",
                "type": "text",
                "text": {"body": "hi"},
                "business_scoped_user_id": "US.123",
                "parent_business_scoped_user_id": "US.ENT.456",
                "username": "@partial",
            }
        ])
        result = normalize_webhook(payload)
        msg = result.messages[0]
        assert msg["from"] == "16315551181"
        assert msg["businessScopedUserId"] == "US.123"
        assert msg["parentBusinessScopedUserId"] == "US.ENT.456"
        assert msg["username"] == "@partial"
        assert msg["kapso"]["direction"] == "inbound"

    def test_webhook_message_pydantic_validates_bsuid_only(self) -> None:
        """Direct WebhookMessage validation against a BSUID-only payload."""
        from kapso_whatsapp import WebhookMessage

        msg = WebhookMessage.model_validate({
            "id": "wamid.x",
            "timestamp": "1700000000",
            "type": "text",
            "text": {"body": "hi"},
            "business_scoped_user_id": "US.999",
            "username": "@x",
        })
        assert msg.from_ is None
        assert msg.business_scoped_user_id == "US.999"
        assert msg.username == "@x"

    # -- WebhookStatus: BSUID-only ---------------------------------------

    def test_status_with_bsuid_recipient_normalizes(self) -> None:
        payload = self._wrap_value({
            "metadata": {"phone_number_id": "111222333"},
            "statuses": [
                {
                    "id": "wamid.s",
                    "status": "delivered",
                    "timestamp": "1700000050",
                    "business_scoped_user_id": "US.42",
                    "username": "@u42",
                    # no `recipient_id`
                }
            ],
        })
        result = normalize_webhook(payload)
        assert len(result.statuses) == 1
        st = result.statuses[0]
        assert st.recipient_id is None
        assert st.business_scoped_user_id == "US.42"
        assert st.username == "@u42"

    def test_webhook_status_pydantic_validates_bsuid_only(self) -> None:
        from kapso_whatsapp import WebhookStatus

        st = WebhookStatus.model_validate({
            "id": "wamid.s",
            "status": "delivered",
            "timestamp": "1700000000",
            "business_scoped_user_id": "US.42",
        })
        assert st.recipient_id is None
        assert st.business_scoped_user_id == "US.42"

    # -- MessageContact: BSUID-only --------------------------------------

    def test_message_contact_pydantic_validates_bsuid_only(self) -> None:
        from kapso_whatsapp import MessageContact

        c = MessageContact.model_validate({
            "input": "+15551234567",
            "business_scoped_user_id": "US.7",
            "username": "@bsuser",
        })
        assert c.wa_id is None
        assert c.business_scoped_user_id == "US.7"

    # -- IdentityChangeEvent: user_id_update raw forward ------------------

    def test_user_id_update_produces_identity_event(self) -> None:
        from kapso_whatsapp.webhooks import IdentityChangeEvent

        payload = self._wrap_value({
            "user_id_update": {
                "previous_wa_id": "15551111111",
                "new_wa_id": None,
                "business_scoped_user_id": "US.new42",
                "timestamp": "1700000099",
            },
        })
        result = normalize_webhook(payload)
        assert len(result.identity_events) == 1
        ev = result.identity_events[0]
        assert isinstance(ev, IdentityChangeEvent)
        assert ev.previous_wa_id == "15551111111"
        assert ev.new_wa_id is None
        assert ev.business_scoped_user_id == "US.new42"
        assert ev.timestamp == "1700000099"

    def test_user_changed_user_id_system_message_produces_identity_event(self) -> None:
        payload = self._wrap_messages([
            {
                "id": "wamid.sys",
                "timestamp": "1700000100",
                "type": "system",
                "system": {
                    "type": "user_changed_user_id",
                    "previous_wa_id": "15551111111",
                    "business_scoped_user_id": "US.7777",
                },
            }
        ])
        result = normalize_webhook(payload)
        assert len(result.identity_events) == 1
        ev = result.identity_events[0]
        assert ev.previous_wa_id == "15551111111"
        assert ev.business_scoped_user_id == "US.7777"
        # The system message should also pull a fallback timestamp from the message itself
        assert ev.timestamp == "1700000100"

    def test_no_identity_events_on_normal_payload(self) -> None:
        """Regression guard: phone-only payloads should NOT produce identity events."""
        payload = self._wrap_messages([
            {
                "id": "wamid.normal",
                "from": "16315551181",
                "timestamp": "1700000200",
                "type": "text",
                "text": {"body": "regular message"},
            }
        ])
        result = normalize_webhook(payload)
        assert result.identity_events == []
