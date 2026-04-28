"""Tests for the template builder helpers (TS SDK parity)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kapso_whatsapp.builders import (
    build_template_definition,
    build_template_payload,
    build_template_send_payload,
)
from kapso_whatsapp.types import TemplateLanguage, TemplateSendPayload

# ---------------------------------------------------------------------------
# build_template_payload — pass-through validator
# ---------------------------------------------------------------------------


class TestBuildTemplatePayload:
    def test_returns_template_send_payload(self) -> None:
        result = build_template_payload(
            name="order", language="en_US",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "Ada"}]}],
        )
        assert isinstance(result, TemplateSendPayload)
        assert result.name == "order"
        assert result.language == "en_US"
        assert len(result.components) == 1

    def test_accepts_language_as_dict(self) -> None:
        result = build_template_payload(
            name="x", language={"code": "en_US"}, components=[],
        )
        assert isinstance(result.language, TemplateLanguage)
        assert result.language.code == "en_US"

    def test_accepts_language_as_template_language(self) -> None:
        lang = TemplateLanguage(code="es")
        result = build_template_payload(name="x", language=lang, components=[])
        assert result.language is lang

    def test_empty_components_default(self) -> None:
        result = build_template_payload(name="x", language="en_US")
        assert result.components == []

    def test_rejects_invalid_parameter_type(self) -> None:
        with pytest.raises(ValidationError):
            build_template_payload(
                name="x", language="en_US",
                components=[{"type": "body", "parameters": [{"type": "bogus"}]}],
            )

    def test_parity_with_direct_construction(self) -> None:
        """build_template_payload should produce the same Pydantic model as
        constructing TemplateSendPayload directly."""
        components = [{"type": "body", "parameters": [{"type": "text", "text": "x"}]}]
        via_builder = build_template_payload(
            name="t", language="en_US", components=components,
        )
        direct = TemplateSendPayload(
            name="t",
            language="en_US",
            components=[
                {"type": "body", "parameters": [{"type": "text", "text": "x"}]}
            ],
        )
        assert via_builder.model_dump() == direct.model_dump()


# ---------------------------------------------------------------------------
# build_template_send_payload — typed shortcut
# ---------------------------------------------------------------------------


class TestBuildTemplateSendPayload:
    def test_body_only(self) -> None:
        result = build_template_send_payload(
            name="order", language="en_US",
            body=[{"type": "text", "text": "Ada"}],
        )
        assert len(result.components) == 1
        assert result.components[0].type == "body"
        assert result.components[0].parameters[0].text == "Ada"

    def test_body_and_header(self) -> None:
        result = build_template_send_payload(
            name="x", language="en_US",
            header=[{"type": "image", "image": {"link": "https://example.com/h.png"}}],
            body=[{"type": "text", "text": "hi"}],
        )
        assert [c.type for c in result.components] == ["header", "body"]

    def test_body_and_buttons(self) -> None:
        result = build_template_send_payload(
            name="x", language="en_US",
            body=[{"type": "text", "text": "hi"}],
            buttons=[
                {
                    "sub_type": "flow",
                    "index": 0,
                    "parameters": [
                        {"type": "action", "action": {"flow_token": "FT_123"}}
                    ],
                }
            ],
        )
        types = [c.type for c in result.components]
        assert types == ["body", "button"]
        button_component = result.components[1]
        assert button_component.sub_type == "flow"
        assert button_component.index == 0

    def test_full_with_header_body_and_buttons(self) -> None:
        result = build_template_send_payload(
            name="full", language="en_US",
            header=[{"type": "text", "text": "Header"}],
            body=[
                {"type": "text", "text": "Ada", "parameter_name": "customer_name"},
                {"type": "text", "text": "#1234", "parameter_name": "order_id"},
            ],
            buttons=[
                {
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [{"type": "payload", "payload": "YES"}],
                }
            ],
        )
        types = [c.type for c in result.components]
        assert types == ["header", "body", "button"]
        body = result.components[1]
        assert len(body.parameters) == 2
        assert body.parameters[0].parameter_name == "customer_name"

    def test_accepts_camel_case_parameter_name(self) -> None:
        """parameterName alias should work via Pydantic populate_by_name."""
        result = build_template_send_payload(
            name="x", language="en_US",
            body=[{"type": "text", "text": "Ada", "parameterName": "customerName"}],
        )
        assert result.components[0].parameters[0].parameter_name == "customerName"

    def test_no_components_when_all_empty(self) -> None:
        result = build_template_send_payload(name="x", language="en_US")
        assert result.components == []

    def test_rejects_invalid_button_subtype(self) -> None:
        with pytest.raises(ValidationError):
            build_template_send_payload(
                name="x", language="en_US",
                buttons=[
                    {"sub_type": "totally_invalid", "index": 0, "parameters": []}
                ],
            )

    def test_body_param_validated_at_build_time(self) -> None:
        with pytest.raises(ValidationError):
            build_template_send_payload(
                name="x", language="en_US",
                body=[{"type": "not_a_real_type"}],
            )


# ---------------------------------------------------------------------------
# build_template_definition — create-time
# ---------------------------------------------------------------------------


class TestBuildTemplateDefinition:
    def test_minimal_utility_template(self) -> None:
        defn = build_template_definition(
            name="order_confirmation",
            category="UTILITY",
            language="en_US",
            components=[{"type": "BODY", "text": "Hello {{1}}", "example": {"body_text": [["Ada"]]}}],
        )
        assert defn["name"] == "order_confirmation"
        assert defn["category"] == "UTILITY"
        assert defn["language"] == "en_US"
        assert len(defn["components"]) == 1

    def test_authentication_template_with_ttl(self) -> None:
        defn = build_template_definition(
            name="auth_code",
            category="AUTHENTICATION",
            language="en_US",
            message_send_ttl_seconds=60,
            components=[
                {"type": "BODY", "add_security_recommendation": True},
                {"type": "FOOTER", "code_expiration_minutes": 10},
                {"type": "BUTTONS", "buttons": [{"type": "OTP", "otp_type": "COPY_CODE"}]},
            ],
        )
        assert defn["message_send_ttl_seconds"] == 60
        assert defn["components"][2]["type"] == "BUTTONS"

    def test_named_parameter_format(self) -> None:
        defn = build_template_definition(
            name="t", category="UTILITY", language="en_US",
            parameter_format="NAMED",
            components=[{"type": "BODY", "text": "Hi {{customer_name}}"}],
        )
        assert defn["parameter_format"] == "NAMED"

    def test_omits_optional_fields_when_not_provided(self) -> None:
        defn = build_template_definition(
            name="x", category="UTILITY", language="en_US",
            components=[{"type": "BODY", "text": "x"}],
        )
        assert "parameter_format" not in defn
        assert "message_send_ttl_seconds" not in defn

    def test_rejects_empty_components(self) -> None:
        with pytest.raises(ValueError, match="components must be a non-empty list"):
            build_template_definition(
                name="x", category="UTILITY", language="en_US", components=[],
            )

    def test_rejects_component_missing_type(self) -> None:
        with pytest.raises(ValueError, match="missing required 'type'"):
            build_template_definition(
                name="x", category="UTILITY", language="en_US",
                components=[{"text": "hi"}],
            )

    def test_rejects_buttons_component_without_buttons_field(self) -> None:
        with pytest.raises(ValueError, match="type=BUTTONS requires a 'buttons' field"):
            build_template_definition(
                name="x", category="UTILITY", language="en_US",
                components=[{"type": "BUTTONS"}],
            )

    def test_rejects_non_dict_component(self) -> None:
        with pytest.raises(ValueError, match="must be a dict"):
            build_template_definition(
                name="x", category="UTILITY", language="en_US",
                components=["not a dict"],  # type: ignore[list-item]
            )
