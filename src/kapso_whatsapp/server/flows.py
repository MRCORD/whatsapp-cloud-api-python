"""
Flow Server-Side Handling

Handle WhatsApp Flow data exchange requests server-side:
- Receive and decrypt flow payloads
- Respond with screen data
- Download and decrypt encrypted flow media
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class FlowServerError(Exception):
    """
    Error during Flow server-side handling.

    Contains HTTP status code and body for proper error responses.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        self.body = json.dumps({"error": message})


@dataclass
class FlowReceiveOptions:
    """Options for receiving a Flow data exchange request."""

    raw_body: bytes
    phone_number_id: str
    get_private_key: Callable[[], Awaitable[str | bytes | None]]
    headers: dict[str, Any] | None = None
    verify_token: (
        Callable[[str, dict[str, str]], bool | Awaitable[bool]] | None
    ) = None


@dataclass
class FlowContext:
    """Parsed Flow data exchange context."""

    action: Literal["DATA_EXCHANGE", "COMPLETE", "BACK"]
    screen: str
    flow_token: str
    form: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowRespondOptions:
    """Options for responding to a Flow request."""

    screen: str
    data: dict[str, Any] | None = None
    status: int = 200
    headers: dict[str, str] | None = None


@dataclass
class EncryptionMetadata:
    """Encryption metadata for Flow media."""

    encrypted_hash: str
    encryption_key: str
    hmac_key: str
    iv: str
    plaintext_hash: str


@dataclass
class DownloadMediaOptions:
    """Options for downloading encrypted Flow media."""

    cdn_url: str
    encryption_metadata: EncryptionMetadata
    http_client: httpx.AsyncClient | None = None


async def receive_flow_event(options: FlowReceiveOptions) -> FlowContext:
    """
    Receive and process a Flow data exchange request.

    Handles both encrypted and unencrypted payloads, verifies tokens,
    and returns a normalized FlowContext.

    Args:
        options: Flow receive configuration

    Returns:
        FlowContext with action, screen, token, form data, etc.

    Raises:
        FlowServerError: On invalid payload, failed decryption, or token verification

    Example:
        >>> async def get_key():
        ...     return os.environ["FLOW_PRIVATE_KEY"]
        >>>
        >>> context = await receive_flow_event(FlowReceiveOptions(
        ...     raw_body=request.body,
        ...     phone_number_id="123456",
        ...     get_private_key=get_key,
        ... ))
        >>> print(f"Screen: {context.screen}, Action: {context.action}")
    """
    # Parse JSON payload
    try:
        text = options.raw_body.decode("utf-8")
        body: dict[str, Any] = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise FlowServerError(400, f"Invalid JSON payload: {e}") from e

    decrypted: dict[str, Any] = body

    # Handle encryption if present
    if body.get("encrypted_flow_data") and body.get("encryption_metadata"):
        metadata = _from_wire_case(body["encryption_metadata"])
        decrypted = await _decrypt_flow_payload(str(body["encrypted_flow_data"]), metadata)

    # Convert to camelCase
    camel = _from_wire_case(decrypted)

    # Parse action
    action_raw = str(camel.get("action", "")).upper()
    if action_raw == "COMPLETE":
        action: Literal["DATA_EXCHANGE", "COMPLETE", "BACK"] = "COMPLETE"
    elif action_raw == "BACK":
        action = "BACK"
    else:
        action = "DATA_EXCHANGE"

    screen = str(camel.get("screen", ""))
    flow_token = str(camel.get("flowToken", camel.get("flow_token", "")))

    # Verify token if verifier provided
    if options.verify_token:
        result = options.verify_token(
            flow_token, {"phoneNumberId": options.phone_number_id}
        )
        if isinstance(result, Awaitable):
            result = await result
        if not result:
            raise FlowServerError(427, "Invalid flow token")

    # Extract form and data
    form_raw = camel.get("form", {})
    data_raw = camel.get("data", {})

    form = _from_wire_case(form_raw) if isinstance(form_raw, dict) else {}
    data = _from_wire_case(data_raw) if isinstance(data_raw, dict) else {}

    return FlowContext(
        action=action,
        screen=screen,
        flow_token=flow_token,
        form=form,
        data=data,
        raw=camel,
    )


def respond_to_flow(
    options: FlowRespondOptions,
) -> dict[str, Any]:
    """
    Build a Flow response for screen navigation.

    Args:
        options: Response configuration

    Returns:
        Dict with status, headers, and body for HTTP response

    Example:
        >>> response = respond_to_flow(FlowRespondOptions(
        ...     screen="CONFIRMATION",
        ...     data={"order_id": "12345", "total": 99.99}
        ... ))
        >>> return Response(
        ...     content=response["body"],
        ...     status_code=response["status"],
        ...     headers=response["headers"]
        ... )
    """
    headers = {"Content-Type": "application/json"}
    if options.headers:
        headers.update(options.headers)

    body = json.dumps({"screen": options.screen, "data": options.data or {}})

    return {
        "status": options.status,
        "headers": headers,
        "body": body,
    }


async def download_and_decrypt_media(options: DownloadMediaOptions) -> bytes:
    """
    Download and decrypt encrypted Flow media.

    Args:
        options: Download configuration with CDN URL and encryption metadata

    Returns:
        Decrypted media bytes

    Raises:
        FlowServerError: On download failure, hash mismatch, or HMAC validation failure

    Example:
        >>> decrypted = await download_and_decrypt_media(DownloadMediaOptions(
        ...     cdn_url="https://cdn.whatsapp.net/...",
        ...     encryption_metadata=EncryptionMetadata(
        ...         encrypted_hash="...",
        ...         encryption_key="...",
        ...         hmac_key="...",
        ...         iv="...",
        ...         plaintext_hash="..."
        ...     )
        ... ))
        >>> with open("output.pdf", "wb") as f:
        ...     f.write(decrypted)
    """
    # Use provided client or create one
    client = options.http_client
    should_close = False
    if client is None:
        client = httpx.AsyncClient()
        should_close = True

    try:
        response = await client.get(options.cdn_url)
        if response.status_code != 200:
            raise FlowServerError(
                response.status_code, f"Failed to download media: {response.status_code}"
            )

        cipher_with_tag = response.content
        meta = _normalize_metadata(options.encryption_metadata)
        plaintext = _decrypt_buffer(cipher_with_tag, meta)
        return plaintext

    finally:
        if should_close:
            await client.aclose()


# =============================================================================
# Private Helpers
# =============================================================================


@dataclass
class _NormalizedMetadata:
    """Internal normalized encryption metadata."""

    encryption_key: bytes
    hmac_key: bytes
    iv: bytes
    encrypted_hash: bytes
    plaintext_hash: bytes


def _normalize_metadata(metadata: EncryptionMetadata) -> _NormalizedMetadata:
    """Convert encryption metadata to bytes."""
    import base64

    def b64_decode(value: str) -> bytes:
        return base64.b64decode(value)

    encryption_key = b64_decode(metadata.encryption_key)
    hmac_key = b64_decode(metadata.hmac_key)
    iv = b64_decode(metadata.iv)
    encrypted_hash = b64_decode(metadata.encrypted_hash)
    plaintext_hash = b64_decode(metadata.plaintext_hash)

    if not encryption_key or not hmac_key or not iv:
        raise FlowServerError(400, "Missing encryption metadata")

    return _NormalizedMetadata(
        encryption_key=encryption_key,
        hmac_key=hmac_key,
        iv=iv,
        encrypted_hash=encrypted_hash,
        plaintext_hash=plaintext_hash,
    )


async def _decrypt_flow_payload(
    encrypted: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Decrypt encrypted flow payload."""
    import base64

    cipher_with_tag = base64.b64decode(encrypted)

    # Convert dict metadata to EncryptionMetadata
    enc_meta = EncryptionMetadata(
        encrypted_hash=str(metadata.get("encryptedHash", metadata.get("encrypted_hash", ""))),
        encryption_key=str(metadata.get("encryptionKey", metadata.get("encryption_key", ""))),
        hmac_key=str(metadata.get("hmacKey", metadata.get("hmac_key", ""))),
        iv=str(metadata.get("iv", "")),
        plaintext_hash=str(metadata.get("plaintextHash", metadata.get("plaintext_hash", ""))),
    )

    meta = _normalize_metadata(enc_meta)
    plaintext = _decrypt_buffer(cipher_with_tag, meta)

    try:
        result: dict[str, Any] = json.loads(plaintext.decode("utf-8"))
        return result
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise FlowServerError(400, f"Unable to parse decrypted payload: {e}") from e


def _decrypt_buffer(cipher_with_tag: bytes, metadata: _NormalizedMetadata) -> bytes:
    """Decrypt buffer with AES-256-CBC and HMAC validation."""
    # Verify encrypted hash
    encrypted_hash = hashlib.sha256(cipher_with_tag).digest()
    if not hmac.compare_digest(encrypted_hash, metadata.encrypted_hash):
        raise FlowServerError(421, "Encrypted payload hash mismatch")

    if len(cipher_with_tag) <= 10:
        raise FlowServerError(421, "Invalid ciphertext length")

    # Split cipher and tag (last 10 bytes)
    cipher = cipher_with_tag[:-10]
    tag = cipher_with_tag[-10:]

    # Verify HMAC (first 10 bytes of HMAC-SHA256)
    computed_hmac = hmac.new(metadata.hmac_key, cipher, hashlib.sha256).digest()[:10]
    if not hmac.compare_digest(tag, computed_hmac):
        raise FlowServerError(432, "HMAC validation failed")

    # Decrypt with AES-256-CBC
    decrypted = Cipher(
        algorithms.AES(metadata.encryption_key),
        modes.CBC(metadata.iv),
        backend=default_backend(),
    ).decryptor()

    unpadded_with_padding = decrypted.update(cipher) + decrypted.finalize()

    # Remove PKCS7 padding
    padding_len = unpadded_with_padding[-1]
    unpadded = unpadded_with_padding[:-padding_len]

    # Verify plaintext hash
    plain_hash = hashlib.sha256(unpadded).digest()
    if not hmac.compare_digest(plain_hash, metadata.plaintext_hash):
        raise FlowServerError(421, "Plaintext hash mismatch")

    return unpadded


def _from_wire_case(obj: Any) -> Any:
    """Convert snake_case keys to camelCase recursively."""
    if isinstance(obj, dict):
        return {_to_camel_key(k): _from_wire_case(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_wire_case(item) for item in obj]
    return obj


def _to_camel_key(key: str) -> str:
    """Convert snake_case to camelCase."""
    if "_" not in key:
        return key
    return re.sub(r"_([a-z0-9])", lambda m: m.group(1).upper(), key)
