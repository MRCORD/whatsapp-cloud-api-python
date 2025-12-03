"""
Webhook Utilities

Functions for handling WhatsApp webhooks:
- Signature verification for security
- Payload normalization for consistent processing
"""

from .normalize import (
    MessageStatusUpdate,
    NormalizedCallEvent,
    NormalizedWebhookResult,
    normalize_webhook,
)
from .verify import verify_signature

__all__ = [
    "verify_signature",
    "normalize_webhook",
    "NormalizedWebhookResult",
    "MessageStatusUpdate",
    "NormalizedCallEvent",
]
