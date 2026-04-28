# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Template builder helpers** for parity with the TS SDK (`@kapso/whatsapp-cloud-api`):
  - `build_template_payload(name=, language=, components=)` — pass-through validator for raw Meta-style components.
  - `build_template_send_payload(name=, language=, body=, header=, buttons=)` — typed shortcut that assembles `components` from flat per-section lists. The high-value ergonomic improvement.
  - `build_template_definition(name=, category=, language=, components=, parameter_format=, message_send_ttl_seconds=)` — create-time validator that returns a dict ready to splat into `client.templates.create()`.
- All three exposed from the top level: `from kapso_whatsapp import build_template_payload, build_template_send_payload, build_template_definition`.
- **BSUID compatibility** for the messaging webhook surface (Meta's business-scoped user ID rollout):
  - `WebhookMessage.from_`, `WebhookStatus.recipient_id`, and `MessageContact.wa_id` are now `Optional` (was required). Username-only users can message without a phone-based identifier.
  - All three models gain `business_scoped_user_id`, `parent_business_scoped_user_id`, `username` Optional fields.
  - `MessageStatusUpdate` and `NormalizedCallEvent` (the dataclasses returned by `normalize_webhook`) gain the same three identity fields.
  - **New `IdentityChangeEvent` dataclass** + `NormalizedWebhookResult.identity_events` list. Surfaces Meta's `user_id_update` field and `user_changed_user_id` system messages on the raw-forward path so consumers can reconcile identity changes against their own store.
  - `webhooks/normalize.py` direction inference falls back to BSUID-only-implies-inbound when phone fields are absent (existing phone-based logic untouched).
  - Platform `Message` model gains both Kapso-shape (`business_scoped_user_id` etc.) and Meta-shape (`from_user_id`, `to_user_id`, etc.) BSUID fields per `docs/platform/whatsapp-data`.
- Public types exported from top level: `IdentityChangeEvent` joins the existing webhook normalization exports.

### Tests
- 22 template-builder tests + 12 BSUID tests = 352 tests total (was 318 in v0.2.0). All passing. mypy + ruff clean.

### Documentation
- New "Template Builders" section in `docs/api-reference.md` with worked examples for all three helpers (raw passthrough, typed shortcut, AUTHENTICATION + NAMED-parameter definitions).
- New "Identity Fields and BSUIDs" section in `docs/webhooks.md` covering the new identity model, the migration checklist, raw-forward identity-change events, and cross-links to all four Kapso BSUID docs.

## [0.2.0] - 2026-04-28

### Added
- **`KapsoPlatformClient`** — new sibling client for the Kapso Platform API at `https://api.kapso.ai/platform/v1`. Manages your Kapso project itself (separate from messaging via `WhatsAppClient`).
- **18 Platform resources, ~87 endpoints**, all live-verified against `api.kapso.ai`:
  - Onboarding: `customers`, `setup_links`, `phone_numbers` (incl. health check), `display_names`, `users`
  - Messaging ops: `messages` (list/get), `conversations` (incl. assignments), `contacts` (incl. erase), `media` (upload)
  - Broadcasts: `broadcasts` (incl. recipients/send/schedule/cancel), `provider_models`
  - Webhooks & logs: `project_webhooks` (incl. test), `webhooks` (phone-number-scoped), `webhook_deliveries`, `api_logs`
  - Data & integrations: `database` (query/insert/upsert/update/delete/get), `integrations` (apps, actions, accounts, connect tokens, action schemas)
  - WhatsApp Flows: `whatsapp_flows` (flows, versions, data endpoint lifecycle, function logs/invocations)
- Every paginated `list(...)` has a matching `iter(...)` async generator that walks all pages automatically. Pagination accepts both `meta.page` and `meta.current_page` field naming.
- `KapsoPlatformClient.request_raw()` returns the full `{data, meta}` envelope; `request()` returns the unwrapped `data` payload; `paginate()` is a generic async iterator for arbitrary list endpoints.
- Top-level exports: `from kapso_whatsapp import KapsoPlatformClient, DEFAULT_PLATFORM_URL`.
- `examples/platform_smoke.py` — read-only health check across all 18 resources.
- `examples/platform_onboarding.py` — customer + setup link end-to-end.
- 208 new tests covering the Platform client and every resource (**265 tests total**, all passing).

### Changed
- Internal: extracted shared HTTP transport (httpx pool + retry/backoff + error categorization) into a private `_HttpCore` class. Both `WhatsAppClient` and `KapsoPlatformClient` delegate to it. `WhatsAppClient` public surface is **unchanged**; existing 57 messaging tests still pass.

### Fixed
- Pydantic models for `ProjectUser`, `Webhook`, and `ProjectWebhook` were too strict for real API responses (required fields the API can return as `null`). Now use `extra="allow"` and optional fields, matching the live shape.

### Documentation
- New `docs/platform-api.md` — comprehensive Platform API reference (612 lines).
- `docs/architecture.md` — updated for two-client topology + shared `_HttpCore`; module tree reflects `platform/` subtree.
- `docs/examples.md` — added Platform examples section (onboarding, CRM sync, scheduled broadcasts, database queries, webhook provisioning, failed-delivery replay, mixing both clients, flow lifecycle).
- `docs/api-reference.md`, `README.md` — link to Platform reference.
- `CONTRIBUTING.md` — Platform fixtures + step-by-step guide for adding a new Platform resource.
- `IMPLEMENTATION_PLAN.md` — v0.2.0 status documented.

### Notes
- The package is still distributed as `kapso_whatsapp`. With Platform support added, the name is slightly inaccurate — a rename to `kapso` is being considered for `1.0`. A deprecation shim will keep existing imports working.
- Tagged as `v0.2.0` on GitHub. Not yet published to PyPI.

## [0.1.4] - 2026-01-24

### Fixed
- **Auto-detect Kapso base URL** - SDK now automatically uses `https://api.kapso.ai/meta/whatsapp` when `kapso_api_key` is provided without explicit `base_url`. Previously, users had to manually specify the base URL, causing 400 errors when forgotten.

### Changed
- Simplified client initialization for Kapso users: `WhatsAppClient(kapso_api_key="xxx")` now works without explicit `base_url`
- Tests updated to verify auto-detection behavior (57 tests passing)

## [0.1.3] - 2025-12-05

### Fixed
- **Kapso proxy URL** - Corrected base URL to `https://api.kapso.ai/meta/whatsapp` (was missing `/meta/whatsapp` path)
- **Exception handling** - Replaced broad `except Exception` with specific exception types for better debugging:
  - `client.py`: JSON parsing now catches `ValueError, TypeError` with explanatory logging
  - `flows.py`: API errors in publish/preview now catch `ValueError, KeyError, TypeError`

### Added
- **DEFAULT_KAPSO_URL** constant - Exported for convenient client configuration
- **Exception docstrings** - Added 27 comprehensive docstrings to exception class methods (`__init__`, `category`, `retry_action`) for improved IDE autocomplete and developer experience

### Changed
- All documentation examples updated with correct Kapso URL (README.md, docs/api-reference.md, docs/examples.md)
- Test fixtures updated to use proper Kapso endpoint
- Test badge updated to reflect 56 passing tests (was 55)

## [0.1.0] - 2025-12-02

### Added

#### Core Features
- **WhatsAppClient** - Main async client with httpx for HTTP operations
- **Pydantic v2 models** - 100+ type-safe models for requests and responses
- **Retry logic** - Automatic retries with exponential backoff for transient errors
- **Error hierarchy** - Specific exception types for different error categories
- **Kapso proxy support** - Automatic detection and enhanced features

#### Message Resources
- `send_text()` - Send text messages with optional URL preview
- `send_image()` - Send images via URL or media ID
- `send_video()` - Send video messages
- `send_audio()` - Send audio messages
- `send_document()` - Send documents with filename
- `send_sticker()` - Send sticker messages
- `send_location()` - Send location with coordinates
- `send_contacts()` - Send contact cards
- `send_template()` - Send template messages with components
- `send_interactive_buttons()` - Interactive button messages
- `send_interactive_list()` - Interactive list messages
- `send_interactive_cta_url()` - Call-to-action URL buttons
- `send_interactive_flow()` - WhatsApp Flow messages
- `send_reaction()` - Add/remove reactions
- `mark_as_read()` - Mark messages as read
- `query()` - Query message history (Kapso only)

#### Media Resource
- `upload()` - Upload media files
- `download()` - Download media content
- `get_url()` - Get media download URL
- `delete()` - Delete uploaded media

#### Templates Resource
- `create()` - Create new templates
- `list()` - List all templates
- `get()` - Get template details
- `update()` - Update templates
- `delete()` - Delete templates

#### Flows Resource
- `create()` - Create new flows
- `get()` - Get flow details
- `update()` - Update flow settings
- `delete()` - Delete flows
- `update_json()` - Update flow JSON definition
- `get_json()` - Get flow JSON
- `publish()` - Publish a flow
- `deprecate()` - Deprecate a flow

#### Phone Numbers Resource
- `register()` - Register phone number
- `deregister()` - Deregister phone number
- `get_business_profile()` - Get business profile
- `update_business_profile()` - Update business profile
- `request_verification_code()` - Request verification code
- `verify_code()` - Verify with code

#### Kapso Proxy Resources
- **Conversations** - `list()` conversations
- **Contacts** - `list()`, `get()`, `update()` contacts
- **Calls** - `list()` call logs

#### Webhooks
- `verify_signature()` - HMAC-SHA256 signature verification
- `normalize_webhook()` - Payload normalization with direction inference
- Direction inference for inbound/outbound messages
- Kapso extension fields support

#### Server-Side Flow Handling
- `receive_flow_event()` - Receive and decrypt flow data
- `respond_to_flow()` - Build flow responses
- `download_and_decrypt_media()` - Download encrypted flow media
- AES-256-GCM decryption support

#### Developer Experience
- Python 3.10+ support
- Full type annotations
- Async context manager support
- Comprehensive test suite (55 tests)
- ruff linting and mypy type checking

### Dependencies
- httpx >= 0.27.0
- pydantic >= 2.0.0
- cryptography >= 42.0.0

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.3 | 2025-12-05 | Fixed Kapso URL, improved exception handling, added docstrings |
| 0.1.0 | 2025-12-02 | Initial release with full API coverage |

## Upgrade Guide

### From flowers-backend

If migrating from the flowers-backend implementation:

1. **Async-only API** - Remove sync wrappers
2. **Pydantic models** - Replace dicts with typed models
3. **Resource-based access** - Use `client.messages.send_text()` instead of `client.send_text()`
4. **Import paths** - Update imports to `from kapso_whatsapp import ...`

```python
# Before (flowers-backend)
from whatsapp import send_text_message
await send_text_message(phone_id, to, body)

# After (kapso-whatsapp)
from kapso_whatsapp import WhatsAppClient
async with WhatsAppClient(access_token=token) as client:
    await client.messages.send_text(phone_number_id, to, body)
```

### Breaking Changes in Future Versions

This section will document breaking changes in future versions.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Links

- [GitHub Repository](https://github.com/gokapso/whatsapp-cloud-api-python)
- [Documentation](https://docs.kapso.ai/docs/whatsapp/python-sdk)
- [Issue Tracker](https://github.com/gokapso/whatsapp-cloud-api-python/issues)
