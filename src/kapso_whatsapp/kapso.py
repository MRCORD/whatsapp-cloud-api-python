"""
Kapso Field Builders

Utilities for building Kapso-specific query fields for message retrieval.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

# All available Kapso message extension fields
KAPSO_MESSAGE_FIELDS: tuple[str, ...] = (
    "direction",
    "status",
    "processing_status",
    "phone_number",
    "has_media",
    "media_data",
    "media_url",
    "whatsapp_conversation_id",
    "contact_name",
    "message_type_data",
    "content",
    "flow_response",
    "flow_token",
    "flow_name",
    "order_text",
)

KapsoMessageField = Literal[
    "direction",
    "status",
    "processing_status",
    "phone_number",
    "has_media",
    "media_data",
    "media_url",
    "whatsapp_conversation_id",
    "contact_name",
    "message_type_data",
    "content",
    "flow_response",
    "flow_token",
    "flow_name",
    "order_text",
]


def build_kapso_fields(fields: Sequence[str] | None = None) -> str:
    """
    Build a kapso() query string for Graph API fields parameter.

    Args:
        fields: Specific fields to include. If None, uses all default fields.

    Returns:
        Formatted kapso() field string

    Example:
        >>> build_kapso_fields()
        'kapso(direction,status,processing_status,...)'
        >>> build_kapso_fields(['direction', 'status'])
        'kapso(direction,status)'
    """
    if fields is None:
        fields = KAPSO_MESSAGE_FIELDS

    # Dedupe and filter empty
    unique = list(dict.fromkeys(f.strip() for f in fields if f.strip()))

    if not unique:
        return "kapso()"

    return f"kapso({','.join(unique)})"


def build_kapso_message_fields(*fields: KapsoMessageField | Sequence[KapsoMessageField]) -> str:
    """
    Build kapso() query string with type-safe field selection.

    Accepts individual fields or sequences of fields, flattens them,
    and builds the query string.

    Args:
        *fields: Field names or sequences of field names

    Returns:
        Formatted kapso() field string

    Example:
        >>> build_kapso_message_fields("direction", "status")
        'kapso(direction,status)'
        >>> build_kapso_message_fields(["direction", "status"], "content")
        'kapso(direction,status,content)'
    """
    flat: list[str] = []
    for field in fields:
        if isinstance(field, str):
            flat.append(field)
        else:
            flat.extend(field)

    if not flat:
        return build_kapso_fields()

    return build_kapso_fields(flat)
