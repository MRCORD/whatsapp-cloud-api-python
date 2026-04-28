"""
Webhook Payload Normalization

Convert raw WhatsApp webhook payloads into a normalized, consistent format.
Handles messages, statuses, calls, and contacts with camelCase conversion.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MessageStatusUpdate:
    """Normalized message status update.

    BSUID rollout: ``recipient_id`` (the target's wa_id) may be null when
    the recipient is identified only by ``business_scoped_user_id``.
    """

    id: str
    status: str
    timestamp: str | None = None
    recipient_id: str | None = None
    business_scoped_user_id: str | None = None
    parent_business_scoped_user_id: str | None = None
    username: str | None = None
    conversation: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedCallEvent:
    """Normalized call event.

    BSUID rollout: ``from_`` / ``to`` may be null on calls from username-only
    users; the user is then identified by ``business_scoped_user_id``.
    """

    event: str | None = None
    call_id: str | None = None
    direction: str | None = None
    status: str | None = None
    from_: str | None = None
    to: str | None = None
    business_scoped_user_id: str | None = None
    parent_business_scoped_user_id: str | None = None
    username: str | None = None
    start_time: int | None = None
    end_time: int | None = None
    duration: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityChangeEvent:
    """Meta identity-reconciliation signal.

    Surfaced only on the *raw Meta forwarding* path (when consumers route
    Meta webhooks directly to their endpoint). The two underlying shapes
    are ``user_id_update`` (a Meta webhook field) and
    ``user_changed_user_id`` (a Meta system message). Both indicate that
    a user's identity was updated; the consumer should reconcile against
    its own identity store rather than create a new contact.

    See: https://docs.kapso.ai/docs/whatsapp/business-scoped-user-ids
    """

    previous_wa_id: str | None = None
    new_wa_id: str | None = None
    business_scoped_user_id: str | None = None
    parent_business_scoped_user_id: str | None = None
    username: str | None = None
    timestamp: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedWebhookResult:
    """
    Normalized webhook payload container.

    Provides consistent access to messages, statuses, calls, contacts,
    and identity-change events regardless of raw webhook structure
    variations.
    """

    object: str | None = None
    phone_number_id: str | None = None
    display_phone_number: str | None = None
    contacts: list[dict[str, Any]] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    statuses: list[MessageStatusUpdate] = field(default_factory=list)
    calls: list[NormalizedCallEvent] = field(default_factory=list)
    identity_events: list[IdentityChangeEvent] = field(default_factory=list)
    raw: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


def normalize_webhook(payload: Any) -> NormalizedWebhookResult:
    """
    Normalize a raw WhatsApp webhook payload.

    Converts snake_case keys to camelCase (Python style),
    extracts messages, statuses, calls, and contacts into
    consistent lists, and preserves raw data for debugging.

    Args:
        payload: Raw webhook payload (dict or JSON string)

    Returns:
        NormalizedWebhookResult with extracted and normalized events

    Example:
        >>> from kapso_whatsapp.webhooks import normalize_webhook
        >>>
        >>> result = normalize_webhook(request.json())
        >>> for message in result.messages:
        ...     print(f"From: {message.get('from')}, Type: {message.get('type')}")
    """
    result = NormalizedWebhookResult()

    if not payload:
        return result

    # Parse JSON string if needed
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return result

    if not isinstance(payload, dict):
        return result

    # Extract top-level object type
    if isinstance(payload.get("object"), str):
        result.object = payload["object"]

    # Process entries
    entries = payload.get("entry", [])
    if not isinstance(entries, list):
        entries = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        changes = entry.get("changes", [])
        if not isinstance(changes, list):
            continue

        for change in changes:
            if not isinstance(change, dict):
                continue

            raw_value = change.get("value")
            if not raw_value or not isinstance(raw_value, dict):
                continue

            # Convert to camelCase
            value = _to_camel_case_deep(raw_value)

            # Track raw by field
            field_key = _to_camel_field(change.get("field"))
            if field_key:
                if field_key not in result.raw:
                    result.raw[field_key] = []
                result.raw[field_key].append(value)

            # Extract metadata
            metadata = value.get("metadata", {})
            if isinstance(metadata, dict):
                if isinstance(metadata.get("phoneNumberId"), str):
                    result.phone_number_id = metadata["phoneNumberId"]
                if isinstance(metadata.get("displayPhoneNumber"), str):
                    result.display_phone_number = metadata["displayPhoneNumber"]

            # Extract contacts
            contacts = value.get("contacts", [])
            if isinstance(contacts, list):
                for contact in contacts:
                    if isinstance(contact, dict):
                        result.contacts.append(_to_camel_case_deep(contact))

            # Extract messages
            messages = value.get("messages", [])
            message_echoes = value.get("messageEchoes", [])
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict):
                        normalized_msg = _normalize_message(msg)
                        _apply_direction(normalized_msg, metadata, is_echo=False)
                        result.messages.append(normalized_msg)

            if isinstance(message_echoes, list):
                for msg in message_echoes:
                    if isinstance(msg, dict):
                        normalized_msg = _normalize_message(msg)
                        _apply_direction(normalized_msg, metadata, is_echo=True)
                        result.messages.append(normalized_msg)

            # Extract statuses
            statuses = value.get("statuses", [])
            if isinstance(statuses, list):
                for status in statuses:
                    if isinstance(status, dict):
                        normalized_status = _to_camel_case_deep(status)
                        result.statuses.append(
                            MessageStatusUpdate(
                                id=str(normalized_status.get("id", "")),
                                status=str(normalized_status.get("status", "")),
                                timestamp=normalized_status.get("timestamp"),
                                recipient_id=normalized_status.get("recipientId"),
                                business_scoped_user_id=normalized_status.get(
                                    "businessScopedUserId"
                                ),
                                parent_business_scoped_user_id=normalized_status.get(
                                    "parentBusinessScopedUserId"
                                ),
                                username=normalized_status.get("username"),
                                conversation=normalized_status.get("conversation"),
                                pricing=normalized_status.get("pricing"),
                                errors=normalized_status.get("errors"),
                                extra={
                                    k: v
                                    for k, v in normalized_status.items()
                                    if k
                                    not in {
                                        "id",
                                        "status",
                                        "timestamp",
                                        "recipientId",
                                        "businessScopedUserId",
                                        "parentBusinessScopedUserId",
                                        "username",
                                        "conversation",
                                        "pricing",
                                        "errors",
                                    }
                                },
                            )
                        )

            # Extract calls
            calls = value.get("calls", [])
            if isinstance(calls, list):
                for call in calls:
                    if isinstance(call, dict):
                        normalized_call = _to_camel_case_deep(call)
                        # Handle wacid -> callId conversion
                        call_id = normalized_call.get("callId") or normalized_call.get(
                            "wacid"
                        )
                        result.calls.append(
                            NormalizedCallEvent(
                                event=normalized_call.get("event"),
                                call_id=call_id,
                                direction=normalized_call.get("direction"),
                                status=normalized_call.get("status"),
                                from_=normalized_call.get("from"),
                                to=normalized_call.get("to"),
                                business_scoped_user_id=normalized_call.get(
                                    "businessScopedUserId"
                                ),
                                parent_business_scoped_user_id=normalized_call.get(
                                    "parentBusinessScopedUserId"
                                ),
                                username=normalized_call.get("username"),
                                start_time=normalized_call.get("startTime"),
                                end_time=normalized_call.get("endTime"),
                                duration=normalized_call.get("duration"),
                                extra={
                                    k: v
                                    for k, v in normalized_call.items()
                                    if k
                                    not in {
                                        "event",
                                        "callId",
                                        "wacid",
                                        "direction",
                                        "status",
                                        "from",
                                        "to",
                                        "businessScopedUserId",
                                        "parentBusinessScopedUserId",
                                        "username",
                                        "startTime",
                                        "endTime",
                                        "duration",
                                    }
                                },
                            )
                        )

            # Extract identity-change events (raw Meta forwarding only).
            # Two shapes appear: a top-level `user_id_update` value field, or a
            # message of type `system` with `system.type == "user_changed_user_id"`.
            for evt in _extract_identity_events(value):
                result.identity_events.append(evt)

    return result


def _normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single message with Kapso extensions."""
    normalized: dict[str, Any] = _to_camel_case_deep(message)

    # Initialize kapso extensions
    kapso: dict[str, Any] = normalized.get("kapso", {})

    # Handle order.text -> orderText
    order = normalized.get("order")
    if isinstance(order, dict) and "text" in order:
        order_text = order.pop("text")
        order["orderText"] = order_text
        kapso["orderText"] = order_text

    # Handle NFM (Flow) replies
    interactive = normalized.get("interactive")
    if isinstance(interactive, dict) and interactive.get("type") == "nfm_reply":
        nfm_reply = interactive.get("nfmReply", {})
        if isinstance(nfm_reply, dict):
            response_json = nfm_reply.get("responseJson")
            if isinstance(response_json, str) and response_json.strip():
                try:
                    parsed = json.loads(response_json)
                    camel = _to_camel_case_deep(parsed)
                    kapso["flowResponse"] = camel
                    if isinstance(camel.get("flowToken"), str):
                        kapso["flowToken"] = camel["flowToken"]
                    if isinstance(nfm_reply.get("name"), str):
                        kapso["flowName"] = nfm_reply["name"]
                except json.JSONDecodeError:
                    pass

    # Only include kapso if it has data
    if kapso:
        normalized["kapso"] = kapso
    elif "kapso" in normalized:
        del normalized["kapso"]

    return normalized


def _apply_direction(
    message: dict[str, Any], metadata: dict[str, Any], is_echo: bool
) -> None:
    """Determine and apply message direction.

    Phone-based inference is the primary path. When ``from`` is null
    (BSUID-only payload from a username-only user), the message is a
    customer-originated inbound by definition (Meta only routes such
    payloads from user → business), so we default to inbound rather
    than leaving direction unset.
    """
    business_candidates: list[str] = []

    phone_number_id = metadata.get("phoneNumberId")
    display_phone_number = metadata.get("displayPhoneNumber")
    context_from = None

    context = message.get("context")
    if isinstance(context, dict):
        context_from = context.get("from")

    if isinstance(phone_number_id, str):
        business_candidates.append(phone_number_id)
    if isinstance(display_phone_number, str):
        business_candidates.append(display_phone_number)
    if isinstance(context_from, str):
        business_candidates.append(context_from)

    business_set = {_normalize_number(n) for n in business_candidates}

    from_norm = _normalize_number(message.get("from", ""))
    to_norm = _normalize_number(message.get("to", ""))

    has_bsuid = bool(message.get("businessScopedUserId"))

    direction: str | None = None

    if is_echo or from_norm and from_norm in business_set:
        direction = "outbound"
    elif to_norm and to_norm in business_set or context_from and _normalize_number(context_from) in business_set or from_norm:
        direction = "inbound"
    elif has_bsuid and not from_norm:
        # BSUID-only payload — phone fields are null. Meta only routes such
        # payloads user → business, so this is an inbound customer message.
        direction = "inbound"

    if direction or is_echo:
        kapso = message.setdefault("kapso", {})
        if direction:
            kapso["direction"] = direction
        if is_echo:
            kapso["source"] = "smb_message_echo"


def _extract_identity_events(value: dict[str, Any]) -> list[IdentityChangeEvent]:
    """Extract Meta identity-reconciliation signals from a webhook value.

    Recognizes two shapes (see Meta docs):

    1. Top-level ``user_id_update`` field (camelCased to ``userIdUpdate``):
       carries ``previousWaId`` / ``newWaId`` / BSUID + timestamp.
    2. A message of type ``system`` with
       ``system.type == "user_changed_user_id"``: carries similar fields
       inside ``system``.

    Both shapes only appear on the raw Meta forwarding path. Kapso's own
    webhook events do not surface these (Kapso reconciles internally).
    """
    events: list[IdentityChangeEvent] = []

    user_id_update = value.get("userIdUpdate")
    if isinstance(user_id_update, dict):
        events.append(_identity_event_from(user_id_update))
    elif isinstance(user_id_update, list):
        for entry in user_id_update:
            if isinstance(entry, dict):
                events.append(_identity_event_from(entry))

    for msg in value.get("messages", []) or []:
        if not isinstance(msg, dict) or msg.get("type") != "system":
            continue
        system = msg.get("system")
        if isinstance(system, dict) and system.get("type") == "user_changed_user_id":
            events.append(_identity_event_from(system, fallback_timestamp=msg.get("timestamp")))

    return events


def _identity_event_from(
    obj: dict[str, Any], fallback_timestamp: str | None = None
) -> IdentityChangeEvent:
    """Build an IdentityChangeEvent from a raw dict, accepting both
    snake_case (Meta) and camelCase (post-normalization) field names."""
    return IdentityChangeEvent(
        previous_wa_id=obj.get("previous_wa_id") or obj.get("previousWaId"),
        new_wa_id=obj.get("new_wa_id") or obj.get("newWaId"),
        business_scoped_user_id=obj.get("business_scoped_user_id")
        or obj.get("businessScopedUserId"),
        parent_business_scoped_user_id=obj.get("parent_business_scoped_user_id")
        or obj.get("parentBusinessScopedUserId"),
        username=obj.get("username"),
        timestamp=obj.get("timestamp") or fallback_timestamp,
        raw=dict(obj),
    )


def _normalize_number(value: str | None) -> str:
    """Extract only digits from a phone number."""
    if not value:
        return ""
    return re.sub(r"[^0-9]", "", value)


def _to_camel_field(field: Any) -> str | None:
    """Convert a field name to camelCase."""
    if not isinstance(field, str) or not field:
        return None
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), field)


# Cache for key conversion
_camel_cache: dict[str, str] = {}


def _to_camel_case_key(key: str) -> str:
    """Convert a single key from snake_case to camelCase."""
    if "_" not in key and "-" not in key:
        return key

    if key in _camel_cache:
        return _camel_cache[key]

    result = re.sub(r"[-_]([a-z0-9])", lambda m: m.group(1).upper(), key)
    _camel_cache[key] = result
    return result


def _to_camel_case_deep(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {_to_camel_case_key(k): _to_camel_case_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_camel_case_deep(item) for item in obj]
    return obj
