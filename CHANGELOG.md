# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
