"""
Webhook Signature Verification

Verify X-Hub-Signature-256 for WhatsApp webhooks using the Meta App Secret.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(
    *,
    app_secret: str,
    raw_body: bytes | str,
    signature_header: str | None,
) -> bool:
    """
    Verify X-Hub-Signature-256 for WhatsApp Webhooks.

    Returns True when the signature matches the request body.
    Uses timing-safe comparison to prevent timing attacks.

    Args:
        app_secret: Your Meta App Secret
        raw_body: Raw request body (bytes or string)
        signature_header: Value of X-Hub-Signature-256 header

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> from kapso_whatsapp.webhooks import verify_signature
        >>>
        >>> # In your webhook handler
        >>> is_valid = verify_signature(
        ...     app_secret="your_app_secret",
        ...     raw_body=request.body,
        ...     signature_header=request.headers.get("X-Hub-Signature-256")
        ... )
        >>> if not is_valid:
        ...     return Response(status_code=401)
    """
    try:
        # Validate inputs
        if not signature_header or not isinstance(signature_header, str):
            return False

        # Parse header format: "sha256=<hex_signature>"
        parts = signature_header.split("=", 1)
        if len(parts) != 2:
            return False

        algo, received_hex = parts
        if algo != "sha256" or not received_hex:
            return False

        # Ensure body is bytes
        body = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body

        # Compute expected signature
        expected_hex = hmac.new(
            key=app_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Timing-safe comparison
        received_bytes = bytes.fromhex(received_hex)
        expected_bytes = bytes.fromhex(expected_hex)

        if len(received_bytes) != len(expected_bytes):
            return False

        return hmac.compare_digest(received_bytes, expected_bytes)

    except (ValueError, TypeError):
        return False
