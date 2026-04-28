"""
Template builder helpers for parity with the TS SDK
(`@kapso/whatsapp-cloud-api`).

Three public functions:

  * `build_template_payload` — accepts raw Meta-style `components`, validates
    via the existing `TemplateSendPayload` Pydantic model, returns a typed
    payload usable by `client.messages.send_template(template=...)`. Pass-
    through validator; equivalent to constructing `TemplateSendPayload`
    directly, but matches the TS SDK's `buildTemplatePayload` for parity.

  * `build_template_send_payload` — typed shortcut. Caller passes `body`,
    `header`, and `buttons` as flat lists; the helper assembles them into
    the Meta `components` structure. The high-value ergonomic improvement
    over hand-rolling `[{"type": "body", "parameters": [...]}]`.

  * `build_template_definition` — used at template *creation* time. Validates
    the components shape and returns a dict ready to be splatted into
    `client.templates.create(business_account_id="…", **defn)`. Covers the
    create-time concerns (parameter_format=NAMED, message_send_ttl_seconds,
    etc.) that the send-side builders don't touch.

All builders delegate to the existing Pydantic models in `types.py` for
validation. Camel-case keys (`parameterName`, `subType`) are accepted via
existing field aliases. The transport layer's `_to_snake_case_deep` handles
case conversion when the payload is sent.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ValidationError

from .types import (
    TemplateComponent,
    TemplateLanguage,
    TemplateParameter,
    TemplateSendPayload,
)

# =============================================================================
# Send-time builders
# =============================================================================


def build_template_payload(
    *,
    name: str,
    language: str | TemplateLanguage | dict[str, Any],
    components: list[dict[str, Any]] | None = None,
) -> TemplateSendPayload:
    """
    Build a send-time template payload from raw Meta-style components.

    Args:
        name: The template name as approved in your WABA.
        language: Either a language code string ("en_US"), a TemplateLanguage,
            or a dict with `code` and optional `policy`.
        components: List of Meta-style component dicts, e.g.
            `[{"type": "body", "parameters": [{"type": "text", "text": "Ada"}]}]`.

    Returns:
        A `TemplateSendPayload` ready to pass to
        `client.messages.send_template(template=...)`.

    Raises:
        pydantic.ValidationError: If any component or parameter is malformed.
    """
    return TemplateSendPayload(
        name=name,
        language=_coerce_language(language),
        components=[TemplateComponent.model_validate(c) for c in (components or [])],
    )


def build_template_send_payload(
    *,
    name: str,
    language: str | TemplateLanguage | dict[str, Any],
    body: list[dict[str, Any]] | None = None,
    header: list[dict[str, Any]] | None = None,
    buttons: list[dict[str, Any]] | None = None,
) -> TemplateSendPayload:
    """
    Typed shortcut: pass body/header/buttons as flat lists; the helper
    assembles them into the Meta `components` structure for you.

    Args:
        name: The template name as approved in your WABA.
        language: Language code string, dict, or `TemplateLanguage`.
        body: Flat list of body parameters, e.g.
            `[{"type": "text", "text": "Ada", "parameter_name": "customer"}]`.
            Accepts camelCase aliases (`parameterName`).
        header: Flat list of header parameters, same shape as body.
        buttons: List of button component dicts, e.g.
            `[{"type": "button", "sub_type": "flow", "index": 0, "parameters": [...]}]`.

    Returns:
        A `TemplateSendPayload` ready for `messages.send_template`.

    Raises:
        pydantic.ValidationError: If any parameter or button is malformed.
    """
    components: list[dict[str, Any]] = []
    if header:
        components.append(
            {"type": "header", "parameters": [_param_dict(p) for p in header]}
        )
    if body:
        components.append(
            {"type": "body", "parameters": [_param_dict(p) for p in body]}
        )
    for button in buttons or []:
        components.append({**button, "type": "button"})

    return build_template_payload(name=name, language=language, components=components)


# =============================================================================
# Create-time builder
# =============================================================================

_CATEGORY = Literal["UTILITY", "MARKETING", "AUTHENTICATION"]
_PARAMETER_FORMAT = Literal["POSITIONAL", "NAMED"]


def build_template_definition(
    *,
    name: str,
    category: _CATEGORY | str,
    language: str,
    components: list[dict[str, Any]],
    parameter_format: _PARAMETER_FORMAT | str | None = None,
    message_send_ttl_seconds: int | None = None,
) -> dict[str, Any]:
    """
    Build a template definition for `client.templates.create()`.

    Validates the component shape (each component needs a `type`; BUTTONS
    components need a `buttons` array) and returns a dict ready to splat
    into the create call. Supports authentication codes, named parameters,
    limited-time offers, catalogs, and any other Meta template shape.

    Args:
        name: Template name (lowercase + underscores per Meta).
        category: One of UTILITY, MARKETING, AUTHENTICATION.
        language: Language code (e.g. "en_US").
        components: List of component dicts. Each needs a `type` field
            (e.g. "BODY", "HEADER", "FOOTER", "BUTTONS", "LIMITED_TIME_OFFER").
        parameter_format: Optional "POSITIONAL" (default) or "NAMED".
        message_send_ttl_seconds: Optional TTL for AUTHENTICATION templates.

    Returns:
        Dict with keys: `name`, `category`, `language`, `components`, and
        optionally `parameter_format` and `message_send_ttl_seconds`. Splat
        into `client.templates.create(business_account_id="…", **defn)`.

    Raises:
        ValueError: If a component is missing required fields.
    """
    if not components:
        raise ValueError("components must be a non-empty list")
    for i, c in enumerate(components):
        if not isinstance(c, dict):
            raise ValueError(f"component[{i}] must be a dict, got {type(c).__name__}")
        if "type" not in c:
            raise ValueError(f"component[{i}] is missing required 'type' field")
        if c["type"] == "BUTTONS" and "buttons" not in c:
            raise ValueError(
                f"component[{i}] type=BUTTONS requires a 'buttons' field"
            )

    definition: dict[str, Any] = {
        "name": name,
        "category": category,
        "language": language,
        "components": components,
    }
    if parameter_format is not None:
        definition["parameter_format"] = parameter_format
    if message_send_ttl_seconds is not None:
        definition["message_send_ttl_seconds"] = message_send_ttl_seconds
    return definition


# =============================================================================
# Helpers
# =============================================================================


def _coerce_language(
    language: str | TemplateLanguage | dict[str, Any],
) -> TemplateLanguage | str:
    """Accept a string code, a TemplateLanguage, or a dict and return what
    `TemplateSendPayload.language` accepts."""
    if isinstance(language, TemplateLanguage):
        return language
    if isinstance(language, dict):
        return TemplateLanguage.model_validate(language)
    return language  # plain string like "en_US"


def _param_dict(p: dict[str, Any] | TemplateParameter) -> dict[str, Any]:
    """Accept either a Pydantic model or a raw dict for a parameter; return a
    validated dict ready to embed in a component. Validation runs here so
    errors surface at build time, not at request time."""
    if isinstance(p, TemplateParameter):
        return p.model_dump(exclude_none=True, by_alias=False)
    try:
        return TemplateParameter.model_validate(p).model_dump(
            exclude_none=True, by_alias=False
        )
    except ValidationError:
        raise
