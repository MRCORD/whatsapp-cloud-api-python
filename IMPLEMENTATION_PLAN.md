# WhatsApp Cloud API Python SDK - Implementation Plan

## Overview

This document outlines the implementation plan for the Python SDK, ported from the TypeScript SDK at `@kapso/whatsapp-cloud-api` with patterns salvaged from the `flowers-backend` implementation.

## Architecture

### Module Structure

```
src/kapso_whatsapp/
├── __init__.py           # Package exports
├── client.py             # Main WhatsAppClient
├── exceptions.py         # Error hierarchy
├── types.py              # Pydantic models
├── kapso.py              # Kapso field helpers
├── resources/
│   ├── __init__.py
│   ├── base.py           # BaseResource class
│   ├── messages.py       # MessagesResource
│   ├── media.py          # MediaResource
│   ├── templates.py      # TemplatesResource
│   ├── flows.py          # FlowsResource
│   ├── phone_numbers.py  # PhoneNumbersResource
│   ├── conversations.py  # ConversationsResource (Kapso)
│   ├── contacts.py       # ContactsResource (Kapso)
│   └── calls.py          # CallsResource (Kapso)
├── webhooks/
│   ├── __init__.py
│   ├── verify.py         # Signature verification
│   └── normalize.py      # Payload normalization
└── server/
    ├── __init__.py
    └── flows.py          # Flow data exchange handling
```

## Implementation Status

### ✅ Completed

#### Core Infrastructure
- [x] Project structure with pyproject.toml
- [x] Pydantic v2 type models (`types.py`)
- [x] Exception hierarchy (`exceptions.py`)
- [x] Main client with httpx (`client.py`)
- [x] Kapso field builders (`kapso.py`)

#### Resources
- [x] Base resource class with Kapso proxy detection
- [x] Messages resource (all message types)
- [x] Media resource (upload, download, delete)
- [x] Templates resource (CRUD operations)
- [x] Flows resource (create, deploy, publish)
- [x] Phone numbers resource (registration, settings)
- [x] Conversations resource (Kapso proxy)
- [x] Contacts resource (Kapso proxy)
- [x] Calls resource (Kapso proxy)

#### Webhooks
- [x] Signature verification (HMAC-SHA256)
- [x] Payload normalization with direction inference
- [x] Status and call event extraction

#### Server-Side
- [x] Flow data exchange handling
- [x] Encrypted payload decryption
- [x] Flow response building
- [x] Media download and decryption

#### Testing
- [x] Test structure with pytest
- [x] Client initialization tests
- [x] Webhook verification tests
- [x] Type validation tests
- [x] Kapso helper tests

### ✅ v0.2.0 — Kapso Platform API (April 2026)

Added a sibling client `KapsoPlatformClient` for the Kapso Platform API (`api.kapso.ai/platform/v1`), separate from messaging via `WhatsAppClient`.

#### Transport Refactor
- [x] Extract shared HTTP transport into private `_HttpCore` (httpx pool, retry-with-backoff, error categorization). Both clients delegate to it. `WhatsAppClient` public surface unchanged.

#### KapsoPlatformClient Foundation
- [x] Flat URL construction `{base}/{path}` (version baked into base URL)
- [x] `X-API-Key` auth header injection
- [x] `request()` / `request_raw()` for unwrapped vs full envelope
- [x] `paginate()` async generator handling `meta.page` and `meta.current_page` quirks
- [x] Lazy-loaded resource properties (18 of them)

#### Platform Resources (~87 endpoints)
- [x] customers (CRUD + iter)
- [x] setup_links (3 endpoints)
- [x] phone_numbers (6 endpoints incl. health check)
- [x] display_names (3 endpoints, phone-number-scoped)
- [x] users (1 endpoint)
- [x] broadcasts (8 endpoints incl. recipients/send/schedule/cancel)
- [x] messages (2 endpoints, list + get)
- [x] conversations (7 endpoints incl. assignments)
- [x] contacts (5 endpoints)
- [x] media (1 endpoint, upload)
- [x] project_webhooks (6 endpoints incl. test)
- [x] webhooks (5 endpoints, phone-number-scoped)
- [x] webhook_deliveries (1 endpoint)
- [x] api_logs (1 endpoint)
- [x] provider_models (1 endpoint, non-paginated)
- [x] database (6 endpoints: query/insert/upsert/update/delete/get)
- [x] integrations (11 endpoints incl. apps, actions, accounts)
- [x] whatsapp_flows (14 endpoints: flows + versions + data endpoint + function observability)

#### Quality
- [x] 208 new tests (265 total, all passing)
- [x] 18/18 resources verified live against `api.kapso.ai/platform/v1`
- [x] mypy clean across 44 source files
- [x] ruff clean across `src/` and `tests/`
- [x] Pydantic models bug-fixed against real responses (User, ProjectWebhook, Webhook)

#### Documentation
- [x] `docs/platform-api.md` — comprehensive Platform reference
- [x] `docs/architecture.md` — updated for two-client topology + `_HttpCore`
- [x] `docs/examples.md` — added Platform examples section
- [x] `docs/api-reference.md` — link to Platform reference
- [x] `README.md` — Platform quickstart + resource table
- [x] `CHANGELOG.md` — v0.2.0 entry

### ✅ v0.3.0 — Template builders + BSUID compatibility (2026-04-28)

Live on PyPI: https://pypi.org/project/kapso-whatsapp-cloud-api/0.3.0/

#### Quality (post-v0.2.0 hardening)
- [x] CI workflow running `examples/platform_smoke.py` nightly against a dedicated test project — `.github/workflows/platform-smoke.yml` (needs `KAPSO_API_TOKEN` repo secret)
- [x] Audit Pydantic strictness on all 18 Platform resources — doc-example regression tests added across all 18 test files (53 new tests). All resource models proved already-permissive enough; no source changes needed beyond the 3 fixed during v0.2.0 smoke
- [x] Tag-triggered PyPI publish via GitHub Actions trusted publishing — `.github/workflows/release.yml` (workflow scaffolded; v0.3.0 actually shipped via manual `python -m build && twine upload` against PyPI API token in `.env`)
- [x] Audit `server/flows.py` test coverage — 17 new tests in `tests/test_server_flows.py` (round-trip encrypt/decrypt, HMAC validation, tampering detection, metadata normalization, response builder, wire-case conversion). Uses AES-256-CBC + HMAC-SHA256 (truncated to 10 bytes) + PKCS7 padding (not AES-GCM as previously noted)

#### TS SDK Parity
- [x] Template builder helpers — `build_template_payload`, `build_template_send_payload`, `build_template_definition` in `src/kapso_whatsapp/builders.py`. 22 tests. Documented in `docs/api-reference.md#template-builders`; examples rewritten in `docs/examples.md`.

#### BSUID Compatibility (Meta business-scoped user ID rollout)
- [x] Messaging webhook types accept null `from`/`wa_id`/`recipient_id`; carry `business_scoped_user_id`, `parent_business_scoped_user_id`, `username` — `WebhookMessage`, `WebhookStatus`, `MessageContact`
- [x] `webhooks/normalize.py` — `MessageStatusUpdate`/`NormalizedCallEvent` carry the same identity fields; new `IdentityChangeEvent` dataclass + `NormalizedWebhookResult.identity_events` for raw-Meta-forward `user_id_update` / `user_changed_user_id` events; direction inference falls back to "BSUID-only implies inbound"
- [x] Platform `Message` accepts both Kapso-shape (`business_scoped_user_id`) and Meta-shape (`from_user_id`/`to_user_id`/etc.) BSUID variants
- [x] `resources/calls.py` returns raw dicts so BSUID fields pass through automatically; doc note added
- [x] 12 BSUID tests in `tests/test_webhooks.py:TestBsuidPayloads` + 3 in `tests/platform/test_messages.py:TestBsuidShapes`
- [x] `docs/webhooks.md` "Identity Fields and BSUIDs" section with migration checklist

#### Documentation
- [x] Cookbook: `kp.database` patterns — `docs/cookbook-database.md` (352 lines, 7 sections)
- [x] Cookbook: `kp.integrations` patterns — `docs/cookbook-integrations.md` (551 lines)
- [x] Deprecation policy doc — `docs/deprecation-policy.md` (232 lines)
- [x] `platform-api.md` corrected to match real signatures (database `**filters`, integrations `app_slug=`, etc.)
- [x] `IntegrationsResource.get(id)` investigated — no underlying API endpoint; documented workaround (filter `list()`)

### 🔄 Pending / Future Work

#### Track-by-waiting (build only when demand surfaces)
- [ ] Sync/blocking client wrapper — wait for 3+ user requests; ship via `from kapso_whatsapp.sync import …` adapter
- [ ] Custom retry policy callback — wait for a real issue; expose `retry_predicate(error) -> bool`

#### Operational
- [ ] Configure `KAPSO_API_TOKEN` repo secret so the nightly smoke workflow runs (workflow YAML is in place)
- [ ] Configure PyPI trusted publishing + GitHub `pypi` environment so the `release.yml` workflow can take over from manual twine uploads at the next bump

#### 1.0 Considerations
- [ ] Package rename `kapso_whatsapp` → `kapso` with deprecation shim that re-exports from old name
- [ ] Cleaner fix for `# type: ignore[valid-type]` in Platform resource files (19 sites — caused by methods named `list` shadowing the builtin in mypy's class scope; pick: alias `_BuiltinList = list` at module level, or rename method to `index()` (breaking))

### Removed from this plan (intentionally)

These were in earlier drafts and have been removed because they're either already done, irrelevant, or pure speculation:

- **End-to-end message flow tests** — vague; respx-mocked tests already exercise full request/response cycles, and "real API E2E" is the same as the CI smoke item above
- **Template rendering tests** — the SDK doesn't render templates client-side; Meta does. Nothing to test.
- **Error handling edge cases** — boilerplate without specifics; either we name the cases or drop it
- **Message payload builders with validation** — Pydantic input models already are this (e.g. `TemplateMessageInput`, `InteractiveButtonsInput`)
- **Request/response interceptors** — YAGNI; no demand. Subclassing `_HttpCore` is the escape hatch if anyone needs it
- **Logging configuration** — the SDK already uses `logging.getLogger(__name__)`; nothing missing
- **Migration guide from flowers-backend** — internal pre-history, no public users have flowers-backend code
- **Framework integration guides (FastAPI, Django)** — generic async Python usage; webhooks doc already shows the pattern
- **Retry policy per-resource overrides** — YAGNI; no demand. Single global retry config covers every actual case

## Key Design Decisions

### 1. Async-First with httpx

The SDK uses httpx instead of aiohttp (from flowers-backend) for:
- Modern async/await patterns
- Connection pooling
- Type annotations support
- Request/response hooks

### 2. Pydantic v2 Over Dataclasses

Upgraded from dataclasses to Pydantic v2 for:
- Runtime validation
- Automatic serialization/deserialization
- Field aliases for camelCase ↔ snake_case
- Better IDE support

### 3. Resource-Based API

Matches TypeScript SDK pattern:
```python
client.messages.send_text(...)
client.templates.create(...)
client.flows.deploy(...)
```

### 4. Lazy Resource Loading

Resources are instantiated on first access to minimize memory:
```python
@property
def messages(self) -> MessagesResource:
    if self._messages is None:
        from .resources.messages import MessagesResource
        self._messages = MessagesResource(self)
    return self._messages
```

### 5. Kapso Proxy Detection

Automatic detection based on base URL:
```python
def is_kapso_proxy(self) -> bool:
    return "kapso.ai" in self._config.base_url
```

Resources check this to enable/disable Kapso-only features.

## TypeScript → Python Mappings

| TypeScript | Python |
|------------|--------|
| Zod schemas | Pydantic models |
| fetch | httpx.AsyncClient |
| ESM exports | `__init__.py` exports |
| vitest | pytest + pytest-asyncio |
| node:crypto | cryptography + hmac |
| Buffer | bytes |
| Promise<T> | Awaitable[T] |

## Testing Strategy

### Unit Tests
- Type validation
- Client initialization
- Helper functions
- Error categorization

### Integration Tests
- Mocked API responses with respx
- Full request/response cycles
- Error handling paths

### Smoke Tests
- Package installation
- Import verification
- Basic client creation

## Release Checklist

- [ ] All tests passing
- [ ] Type checking with mypy
- [ ] Linting with ruff
- [ ] README updated
- [ ] CHANGELOG created
- [ ] Version bumped
- [ ] PyPI publishing configured
- [ ] GitHub Actions for CI/CD

## Dependencies

### Runtime
- `httpx>=0.27.0` - Async HTTP client
- `pydantic>=2.0.0` - Data validation
- `cryptography>=42.0.0` - Flow encryption

### Development
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.24.0` - Async test support
- `respx>=0.21.0` - httpx mocking
- `ruff>=0.5.0` - Linting
- `mypy>=1.10.0` - Type checking

## Migration from flowers-backend

### What Was Salvaged
- Retry logic patterns
- Error categorization concept
- Message type handling
- Webhook normalization structure

### What Was Upgraded
- aiohttp → httpx
- dataclasses → Pydantic v2
- Manual validation → Pydantic validators
- Basic errors → Rich error hierarchy
- Single file → Modular structure

### Breaking Changes from flowers-backend
- Async-only API (no sync fallback)
- Pydantic models instead of dicts
- Resource-based organization
- Different import paths
