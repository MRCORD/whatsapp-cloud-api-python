"""Tests for Kapso helper functions."""

from __future__ import annotations

from kapso_whatsapp.kapso import (
    KAPSO_MESSAGE_FIELDS,
    build_kapso_fields,
    build_kapso_message_fields,
)


class TestKapsoFields:
    """Test Kapso field constants and builders."""

    def test_default_fields_exist(self) -> None:
        """Should have all expected default fields."""
        expected = {
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
        }
        assert set(KAPSO_MESSAGE_FIELDS) == expected


class TestBuildKapsoFields:
    """Test build_kapso_fields function."""

    def test_with_default_fields(self) -> None:
        """Should use all default fields when none specified."""
        result = build_kapso_fields()
        assert result.startswith("kapso(")
        assert result.endswith(")")
        # Should contain multiple fields
        inner = result[6:-1]
        fields = inner.split(",")
        assert len(fields) == len(KAPSO_MESSAGE_FIELDS)

    def test_with_specific_fields(self) -> None:
        """Should use only specified fields."""
        result = build_kapso_fields(["direction", "status"])
        assert result == "kapso(direction,status)"

    def test_with_empty_list(self) -> None:
        """Should return empty kapso for empty list."""
        result = build_kapso_fields([])
        assert result == "kapso()"

    def test_deduplicates_fields(self) -> None:
        """Should deduplicate repeated fields."""
        result = build_kapso_fields(["direction", "direction", "status"])
        assert result == "kapso(direction,status)"

    def test_strips_whitespace(self) -> None:
        """Should strip whitespace from fields."""
        result = build_kapso_fields(["  direction  ", "status"])
        assert result == "kapso(direction,status)"

    def test_filters_empty_strings(self) -> None:
        """Should filter empty strings."""
        result = build_kapso_fields(["direction", "", "  ", "status"])
        assert result == "kapso(direction,status)"


class TestBuildKapsoMessageFields:
    """Test build_kapso_message_fields function."""

    def test_with_individual_fields(self) -> None:
        """Should accept individual field arguments."""
        result = build_kapso_message_fields("direction", "status")
        assert result == "kapso(direction,status)"

    def test_with_sequence(self) -> None:
        """Should accept sequence of fields."""
        result = build_kapso_message_fields(["direction", "status"])
        assert result == "kapso(direction,status)"

    def test_with_mixed_args(self) -> None:
        """Should accept mixed individual and sequence args."""
        result = build_kapso_message_fields(["direction", "status"], "content")
        assert result == "kapso(direction,status,content)"

    def test_empty_returns_default(self) -> None:
        """Should return default fields when called with no args."""
        result = build_kapso_message_fields()
        assert result.startswith("kapso(")
        # Should have all fields
        inner = result[6:-1]
        fields = inner.split(",")
        assert len(fields) == len(KAPSO_MESSAGE_FIELDS)
