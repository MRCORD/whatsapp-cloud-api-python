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

### 🔄 Pending / Future Work

#### Phase 2: Enhanced Testing
- [ ] Integration tests with mocked API
- [ ] End-to-end message flow tests
- [ ] Template rendering tests
- [ ] Flow encryption/decryption tests
- [ ] Error handling edge cases

#### Phase 3: Additional Features
- [ ] Template definition builder (TypeScript SDK parity)
- [ ] Message payload builders with validation
- [ ] Retry policy customization
- [ ] Request/response interceptors
- [ ] Logging configuration

#### Phase 4: Documentation
- [ ] API reference documentation
- [ ] Usage examples per resource
- [ ] Migration guide from flowers-backend
- [ ] Framework integration guides (FastAPI, Django)

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
