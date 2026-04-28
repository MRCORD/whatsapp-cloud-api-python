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

### 🔄 Pending / Future Work

#### Quality
- [ ] CI workflow running `examples/platform_smoke.py` nightly against a dedicated test project (catches Pydantic-vs-API drift like the three we fixed in v0.2.0)
- [ ] Audit Pydantic strictness on all 18 Platform resources — sample real responses for each, mark fields optional / add `extra="allow"` where the API returns nulls or extra keys
- [ ] Tag-triggered PyPI publish via GitHub Actions trusted publishing (currently the v0.2.0 tag is pushed but PyPI publish is manual)
- [ ] Audit `server/flows.py` test coverage for encryption/decryption (AES-GCM-128 over Meta's flow data exchange)

#### TS SDK Parity
- [ ] Template definition builder — verify the TS SDK actually has one before committing to it

#### Documentation
- [ ] Cookbook: `kp.database` patterns (idempotent upsert, schema migrations, query composition)
- [ ] Cookbook: `kp.integrations` patterns (OAuth connect flow, action prop config, account discovery)
- [ ] Deprecation policy doc — what counts as a breaking change vs a minor; how long shims live

#### Track-by-waiting (build only when demand surfaces)
- [ ] Sync/blocking client wrapper — wait for 3+ user requests; ship via `from kapso_whatsapp.sync import …` adapter
- [ ] Custom retry policy callback — wait for a real issue; expose `retry_predicate(error) -> bool`

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
