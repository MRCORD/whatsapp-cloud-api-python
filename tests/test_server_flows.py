"""
Tests for kapso_whatsapp.server.flows.

Covers the encrypt/decrypt round-trip (AES-256-CBC + HMAC-SHA256 truncated
to 10 bytes, PKCS7 padding), the response-builder helper, and the
camelCase wire-format converter. Crypto vectors are generated locally
inside each test so we don't depend on Meta-supplied fixtures.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from kapso_whatsapp.server.flows import (
    EncryptionMetadata,
    FlowRespondOptions,
    FlowServerError,
    _decrypt_buffer,
    _from_wire_case,
    _normalize_metadata,
    _to_camel_key,
    respond_to_flow,
)


def _build_encrypted_payload(plaintext: bytes, key: bytes, iv: bytes, hmac_key: bytes) -> tuple[bytes, EncryptionMetadata]:
    """Build a cipher+tag blob and EncryptionMetadata that match what _decrypt_buffer expects."""
    # PKCS7 pad to AES block size (16 bytes)
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)

    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).encryptor()
    cipher = encryptor.update(padded) + encryptor.finalize()

    # Truncated HMAC tag (first 10 bytes, matches the impl)
    tag = hmac.new(hmac_key, cipher, hashlib.sha256).digest()[:10]
    cipher_with_tag = cipher + tag

    metadata = EncryptionMetadata(
        encrypted_hash=base64.b64encode(hashlib.sha256(cipher_with_tag).digest()).decode(),
        encryption_key=base64.b64encode(key).decode(),
        hmac_key=base64.b64encode(hmac_key).decode(),
        iv=base64.b64encode(iv).decode(),
        plaintext_hash=base64.b64encode(hashlib.sha256(plaintext).digest()).decode(),
    )
    return cipher_with_tag, metadata


class TestDecryptBuffer:
    def test_round_trip_recovers_plaintext(self) -> None:
        key = os.urandom(32)
        iv = os.urandom(16)
        hmac_key = os.urandom(32)
        plaintext = b'{"action":"INIT","screen":"WELCOME"}'

        cipher_with_tag, metadata = _build_encrypted_payload(plaintext, key, iv, hmac_key)
        normalized = _normalize_metadata(metadata)

        recovered = _decrypt_buffer(cipher_with_tag, normalized)
        assert recovered == plaintext

    def test_rejects_tampered_ciphertext(self) -> None:
        key = os.urandom(32)
        iv = os.urandom(16)
        hmac_key = os.urandom(32)
        plaintext = b"sensitive payload"

        cipher_with_tag, metadata = _build_encrypted_payload(plaintext, key, iv, hmac_key)
        # Flip a byte in the ciphertext (not in the tag)
        tampered = bytearray(cipher_with_tag)
        tampered[0] ^= 0x01
        normalized = _normalize_metadata(metadata)

        # The encrypted_hash check fires first; either way it raises FlowServerError.
        with pytest.raises(FlowServerError):
            _decrypt_buffer(bytes(tampered), normalized)

    def test_rejects_when_hmac_doesnt_match(self) -> None:
        key = os.urandom(32)
        iv = os.urandom(16)
        hmac_key = os.urandom(32)
        plaintext = b"x"

        cipher_with_tag, metadata = _build_encrypted_payload(plaintext, key, iv, hmac_key)

        # Build new metadata that re-blesses the (modified) ciphertext's encrypted_hash
        # but keeps the WRONG hmac_key — forces the HMAC check to be the failure point.
        tampered_cipher = bytearray(cipher_with_tag)
        tampered_cipher[-11] ^= 0x01  # mutate the last byte of the cipher (not the tag)
        bad_metadata = EncryptionMetadata(
            encrypted_hash=base64.b64encode(hashlib.sha256(bytes(tampered_cipher)).digest()).decode(),
            encryption_key=metadata.encryption_key,
            hmac_key=metadata.hmac_key,
            iv=metadata.iv,
            plaintext_hash=metadata.plaintext_hash,
        )
        normalized = _normalize_metadata(bad_metadata)

        with pytest.raises(FlowServerError) as exc:
            _decrypt_buffer(bytes(tampered_cipher), normalized)
        assert exc.value.status in (421, 432)  # either hash or HMAC mismatch

    def test_rejects_too_short_ciphertext(self) -> None:
        key = os.urandom(32)
        iv = os.urandom(16)
        hmac_key = os.urandom(32)

        # 5-byte fake cipher — well under the 10-byte minimum.
        bogus = b"\x00" * 5
        metadata = EncryptionMetadata(
            encrypted_hash=base64.b64encode(hashlib.sha256(bogus).digest()).decode(),
            encryption_key=base64.b64encode(key).decode(),
            hmac_key=base64.b64encode(hmac_key).decode(),
            iv=base64.b64encode(iv).decode(),
            plaintext_hash=base64.b64encode(hashlib.sha256(b"").digest()).decode(),
        )
        normalized = _normalize_metadata(metadata)

        with pytest.raises(FlowServerError) as exc:
            _decrypt_buffer(bogus, normalized)
        assert exc.value.status == 421


class TestNormalizeMetadata:
    def test_decodes_base64_fields(self) -> None:
        metadata = EncryptionMetadata(
            encrypted_hash=base64.b64encode(b"a" * 32).decode(),
            encryption_key=base64.b64encode(b"b" * 32).decode(),
            hmac_key=base64.b64encode(b"c" * 32).decode(),
            iv=base64.b64encode(b"d" * 16).decode(),
            plaintext_hash=base64.b64encode(b"e" * 32).decode(),
        )
        normalized = _normalize_metadata(metadata)
        assert normalized.encryption_key == b"b" * 32
        assert normalized.iv == b"d" * 16

    def test_rejects_empty_keys(self) -> None:
        metadata = EncryptionMetadata(
            encrypted_hash="",
            encryption_key="",
            hmac_key="",
            iv="",
            plaintext_hash="",
        )
        with pytest.raises(FlowServerError) as exc:
            _normalize_metadata(metadata)
        assert exc.value.status == 400


class TestRespondToFlow:
    def test_returns_status_headers_body(self) -> None:
        result = respond_to_flow(FlowRespondOptions(screen="WELCOME"))
        assert result["status"] == 200
        assert result["headers"]["Content-Type"] == "application/json"
        assert json.loads(result["body"]) == {"screen": "WELCOME", "data": {}}

    def test_includes_data(self) -> None:
        result = respond_to_flow(FlowRespondOptions(
            screen="CONFIRMATION",
            data={"order_id": "12345", "total": 99.99},
        ))
        assert json.loads(result["body"]) == {
            "screen": "CONFIRMATION",
            "data": {"order_id": "12345", "total": 99.99},
        }

    def test_custom_headers_merge(self) -> None:
        result = respond_to_flow(FlowRespondOptions(
            screen="X",
            headers={"X-Trace-Id": "abc"},
        ))
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["headers"]["X-Trace-Id"] == "abc"

    def test_custom_status(self) -> None:
        result = respond_to_flow(FlowRespondOptions(screen="X", status=201))
        assert result["status"] == 201


class TestWireCaseConversion:
    def test_to_camel_key_no_underscore(self) -> None:
        assert _to_camel_key("alreadyCamel") == "alreadyCamel"
        assert _to_camel_key("plain") == "plain"

    def test_to_camel_key_simple(self) -> None:
        assert _to_camel_key("foo_bar") == "fooBar"
        assert _to_camel_key("snake_case_string") == "snakeCaseString"

    def test_to_camel_key_with_digits(self) -> None:
        assert _to_camel_key("v_2") == "v2"
        assert _to_camel_key("foo_2_bar") == "foo2Bar"

    def test_from_wire_case_dict(self) -> None:
        assert _from_wire_case({"flow_token": "x", "screen_id": "y"}) == {
            "flowToken": "x",
            "screenId": "y",
        }

    def test_from_wire_case_nested(self) -> None:
        result = _from_wire_case({
            "outer_key": {"inner_key": [1, 2, {"deep_key": "v"}]},
        })
        assert result == {"outerKey": {"innerKey": [1, 2, {"deepKey": "v"}]}}

    def test_from_wire_case_passthrough_non_collections(self) -> None:
        assert _from_wire_case("string") == "string"
        assert _from_wire_case(42) == 42
        assert _from_wire_case(None) is None


class TestFlowServerError:
    def test_carries_status_and_body(self) -> None:
        err = FlowServerError(421, "boom")
        assert err.status == 421
        assert err.headers == {"Content-Type": "application/json"}
        assert json.loads(err.body) == {"error": "boom"}
