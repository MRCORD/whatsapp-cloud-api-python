# Architecture

System architecture, design decisions, and diagrams for the Kapso WhatsApp Cloud API Python SDK.

## Table of Contents

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Client Architecture](#client-architecture)
- [Resource Pattern](#resource-pattern)
- [Request Flow](#request-flow)
- [Error Handling](#error-handling)
- [Webhook Processing](#webhook-processing)
- [Flow Data Exchange](#flow-data-exchange)
- [Design Decisions](#design-decisions)

---

## Overview

The SDK ships **two clients** that share an internal HTTP transport:

- **`WhatsAppClient`** — sends/receives WhatsApp messages via Meta Graph or the Kapso Meta-proxy (`graph.facebook.com` / `api.kapso.ai/meta/whatsapp`). URL shape: `{base}/{graph_version}/{path}`. Auth: Bearer token or `X-API-Key`.
- **`KapsoPlatformClient`** — manages the Kapso project itself (customers, broadcasts, webhooks, database, integrations, WhatsApp Flow lifecycle, …) at `api.kapso.ai/platform/v1`. URL shape: `{base}/{path}` (version baked into base). Auth: `X-API-Key` only. Response envelope: `{"data": ..., "meta": {...}}`.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Your Application                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                  │                                          │
                  ▼                                          ▼
┌──────────────────────────────┐       ┌──────────────────────────────────────┐
│       WhatsAppClient         │       │        KapsoPlatformClient           │
│  Messaging via Meta / Kapso  │       │   Project mgmt via api.kapso.ai      │
│  ┌────────────────────────┐  │       │  ┌────────────────────────────────┐  │
│  │ Resources              │  │       │  │ 18 Resources                   │  │
│  │  messages, media,      │  │       │  │  customers, setup_links,       │  │
│  │  templates, flows,     │  │       │  │  phone_numbers, display_names, │  │
│  │  phone_numbers,        │  │       │  │  users, broadcasts, messages,  │  │
│  │  conversations,        │  │       │  │  conversations, contacts,      │  │
│  │  contacts, calls       │  │       │  │  media, project_webhooks,      │  │
│  │  (Kapso proxy only)    │  │       │  │  webhooks, webhook_deliveries, │  │
│  │                        │  │       │  │  api_logs, provider_models,    │  │
│  │                        │  │       │  │  database, integrations,       │  │
│  │                        │  │       │  │  whatsapp_flows                │  │
│  └────────────────────────┘  │       │  └────────────────────────────────┘  │
│  ┌────────────────────────┐  │       │  ┌────────────────────────────────┐  │
│  │ Webhooks (verify +     │  │       │  │ Pagination helper              │  │
│  │ normalize)             │  │       │  │ (paginate(), iter())           │  │
│  └────────────────────────┘  │       │  └────────────────────────────────┘  │
│  ┌────────────────────────┐  │       │  ┌────────────────────────────────┐  │
│  │ Server-side flows      │  │       │  │ Envelope unwrapping            │  │
│  │ (decrypt/respond)      │  │       │  │ (request() / request_raw())    │  │
│  └────────────────────────┘  │       │  └────────────────────────────────┘  │
└──────────────┬───────────────┘       └─────────────────┬────────────────────┘
               │                                         │
               └────────────────┬────────────────────────┘
                                ▼
              ┌──────────────────────────────────────┐
              │   _HttpCore (private, shared)        │
              │   • httpx connection pool            │
              │   • retry-with-backoff               │
              │   • Retry-After honoring             │
              │   • error categorization             │
              └──────────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────────┐
              ▼                 ▼                     ▼
   ┌──────────────────┐  ┌────────────────┐  ┌──────────────────────┐
   │ Meta Graph API   │  │  Kapso Meta-   │  │  Kapso Platform API  │
   │graph.facebook.com│  │  proxy         │  │  api.kapso.ai/       │
   │                  │  │  api.kapso.ai/ │  │  platform/v1         │
   │                  │  │  meta/whatsapp │  │                      │
   └──────────────────┘  └────────────────┘  └──────────────────────┘
```

The HTTP core is private (`_http.py`). Each client builds its own URLs and handles its own response shape, but they share retry logic, auth header injection, error mapping, and connection pooling. Improvements to the transport land once and benefit both clients.

---

## Module Structure

```
src/kapso_whatsapp/
├── __init__.py           # Package exports — both clients, version
├── _http.py              # Private: shared httpx pool, retry, error mapping
├── client.py             # WhatsAppClient (delegates transport to _HttpCore)
├── exceptions.py         # Error hierarchy and categorization (shared)
├── types.py              # Pydantic models for messaging surface
├── kapso.py              # Kapso field helpers
│
├── resources/            # WhatsAppClient resource modules
│   ├── __init__.py
│   ├── base.py           # BaseResource
│   ├── messages.py       # send/read messages
│   ├── media.py          # upload/download media
│   ├── templates.py      # template management
│   ├── flows.py          # WhatsApp Flow management (messaging side)
│   ├── phone_numbers.py  # phone number config
│   ├── conversations.py  # conversation listing (Kapso proxy)
│   ├── contacts.py       # contact CRUD (Kapso proxy)
│   └── calls.py          # call logs (Kapso proxy)
│
├── platform/             # KapsoPlatformClient — Kapso project management
│   ├── __init__.py
│   ├── client.py         # KapsoPlatformClient (delegates to _HttpCore)
│   ├── types.py          # PlatformMeta, PaginatedResponse, Customer
│   └── resources/        # 18 resource modules, each with its own Pydantic models
│       ├── base.py       # PlatformBaseResource
│       ├── customers.py
│       ├── setup_links.py
│       ├── phone_numbers.py
│       ├── display_names.py
│       ├── users.py
│       ├── broadcasts.py
│       ├── messages.py
│       ├── conversations.py
│       ├── contacts.py
│       ├── media.py
│       ├── project_webhooks.py
│       ├── webhooks.py
│       ├── webhook_deliveries.py
│       ├── api_logs.py
│       ├── provider_models.py
│       ├── database.py
│       ├── integrations.py
│       └── whatsapp_flows.py
│
├── webhooks/             # Webhook handling (messaging side)
│   ├── __init__.py
│   ├── verify.py         # HMAC-SHA256 signature verification
│   └── normalize.py      # Payload normalization with direction inference
│
└── server/               # Server-side features
    ├── __init__.py
    └── flows.py          # Flow data exchange (encrypted payload handling)
```

---

## Client Architecture

### WhatsAppClient

The main client manages configuration, HTTP transport, and resource access.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            WhatsAppClient                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Configuration (Pydantic)                                               │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ access_token | kapso_api_key | base_url | timeout | max_retries   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  HTTP Client (httpx.AsyncClient)                                        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Connection pooling | Timeouts | Headers | Base URL                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Request Method (_request)                                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Rate limit handling | Retry logic | Error conversion | Logging    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Lazy-Loaded Resources                                                  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ messages | media | templates | flows | phone_numbers | ...         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Lazy Resource Loading

Resources are instantiated on first access to minimize memory usage:

```python
@property
def messages(self) -> MessagesResource:
    if self._messages is None:
        self._messages = MessagesResource(self)
    return self._messages
```

---

## Resource Pattern

All resources follow a consistent pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            BaseResource                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Properties                                                             │
│  • client: WhatsAppClient                                               │
│  • is_kapso: bool (detected from URL)                                   │
│                                                                          │
│  Methods                                                                │
│  • _build_url(endpoint) → Full URL with version                         │
│  • _request(method, url, **kwargs) → Delegates to client                │
│  • _require_kapso() → Raises if not using Kapso proxy                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Messages   │ │    Media    │ │  Templates  │
            │  Resource   │ │  Resource   │ │  Resource   │
            ├─────────────┤ ├─────────────┤ ├─────────────┤
            │ send_text() │ │  upload()   │ │  create()   │
            │ send_image()│ │  download() │ │  list()     │
            │ send_video()│ │  get_url()  │ │  get()      │
            │ send_audio()│ │  delete()   │ │  update()   │
            │ send_tmpl() │ └─────────────┘ │  delete()   │
            │ interactive │                 └─────────────┘
            └─────────────┘
```

---

## Request Flow

### Standard Request

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User    │     │   Resource   │     │   Client     │     │   httpx      │
│  Code    │     │   Method     │     │   _request   │     │   Client     │
└────┬─────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
     │                  │                    │                    │
     │  send_text()     │                    │                    │
     │─────────────────►│                    │                    │
     │                  │                    │                    │
     │                  │  Validate input    │                    │
     │                  │  (Pydantic)        │                    │
     │                  │                    │                    │
     │                  │  _request()        │                    │
     │                  │───────────────────►│                    │
     │                  │                    │                    │
     │                  │                    │  Build headers     │
     │                  │                    │  Add auth token    │
     │                  │                    │                    │
     │                  │                    │  request()         │
     │                  │                    │───────────────────►│
     │                  │                    │                    │
     │                  │                    │◄───────────────────│
     │                  │                    │  Response          │
     │                  │                    │                    │
     │                  │                    │  Check status      │
     │                  │                    │  Parse errors      │
     │                  │                    │                    │
     │                  │◄───────────────────│                    │
     │                  │  dict | exception  │                    │
     │                  │                    │                    │
     │                  │  Parse response    │                    │
     │                  │  (Pydantic)        │                    │
     │                  │                    │                    │
     │◄─────────────────│                    │                    │
     │  SendMessageResponse                  │                    │
     │                  │                    │                    │
```

### Retry Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Retry Logic                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Attempt 1                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Request → RateLimitError (429)                                  │   │
│  │  Wait: retry_after or backoff * 2^0 = 1s                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  Attempt 2                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Request → NetworkError                                          │   │
│  │  Wait: backoff * 2^1 = 2s                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  Attempt 3                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Request → Success ✓                                             │   │
│  │  Return response                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Non-Retryable Errors (immediate failure):                              │
│  • AuthenticationError (401)                                            │
│  • ValidationError (400)                                                │
│  • MessageWindowError (131026)                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Error Hierarchy

```
Exception
└── WhatsAppAPIError
    ├── AuthenticationError       # 401, invalid tokens
    ├── RateLimitError            # 429, rate limits
    │   └── retry_after: float    # Seconds to wait
    ├── ValidationError           # 400, bad request
    ├── NetworkError              # Connection failed
    ├── TimeoutError              # Request timeout
    ├── MessageWindowError        # 24h window expired
    └── KapsoProxyRequiredError   # Feature needs Kapso
```

### Error Categorization

```python
from kapso_whatsapp.exceptions import categorize_error, ErrorCategory

# Categories
ErrorCategory.AUTHENTICATION  # Token issues
ErrorCategory.RATE_LIMIT      # Too many requests
ErrorCategory.VALIDATION      # Invalid input
ErrorCategory.TEMPORARY       # Transient errors
ErrorCategory.PERMANENT       # Cannot retry
ErrorCategory.UNKNOWN         # Unclassified
```

---

## Webhook Processing

### Signature Verification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Signature Verification                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Input                                                                  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ X-Hub-Signature-256: sha256=abc123def456...                        │ │
│  │ Body: {"object": "whatsapp_business_account", ...}                 │ │
│  │ App Secret: your_app_secret                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Process                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Parse header: algorithm=sha256, signature=abc123...             │ │
│  │ 2. Compute: HMAC-SHA256(app_secret, body)                          │ │
│  │ 3. Compare: hmac.compare_digest(computed, received)                │ │
│  │ 4. Return: True if match, False otherwise                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Payload Normalization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Payload Normalization                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Input (Nested Meta Structure)                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                   │ │
│  │   "object": "whatsapp_business_account",                           │ │
│  │   "entry": [{                                                       │ │
│  │     "changes": [{                                                   │ │
│  │       "value": {                                                    │ │
│  │         "messages": [...],                                          │ │
│  │         "statuses": [...]                                           │ │
│  │       }                                                             │ │
│  │     }]                                                              │ │
│  │   }]                                                                │ │
│  │ }                                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  Processing                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Extract messages and statuses from nested structure             │ │
│  │ 2. Convert snake_case → camelCase                                  │ │
│  │ 3. Merge metadata (phone_number_id) into each message              │ │
│  │ 4. Infer direction (inbound/outbound)                              │ │
│  │ 5. Add Kapso extension fields                                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  Output (Flat Structure)                                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ NormalizedWebhookResult(                                            │ │
│  │   messages=[                                                        │ │
│  │     {"id": "...", "from": "...", "type": "text",                   │ │
│  │      "kapso": {"direction": "inbound"}}                            │ │
│  │   ],                                                                │ │
│  │   statuses=[WebhookStatus(id="...", status="delivered")],          │ │
│  │   calls=[]                                                          │ │
│  │ )                                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Flow Data Exchange

### Encryption/Decryption Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Flow Data Exchange                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Incoming Request (Encrypted)                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                   │ │
│  │   "encrypted_flow_data": "base64_encrypted_payload",               │ │
│  │   "encryption_metadata": {                                          │ │
│  │     "key": "encrypted_aes_key",                                    │ │
│  │     "iv": "initialization_vector"                                  │ │
│  │   }                                                                 │ │
│  │ }                                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  Decryption Process                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Load private key (PEM format)                                   │ │
│  │ 2. Decrypt AES key using RSA-OAEP                                  │ │
│  │ 3. Decrypt payload using AES-256-GCM                               │ │
│  │ 4. Verify HMAC signature                                           │ │
│  │ 5. Parse JSON payload                                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  FlowContext                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ screen: "FORM_SCREEN"                                              │ │
│  │ action: "navigate"                                                 │ │
│  │ form: {"field1": "value1", "field2": "value2"}                     │ │
│  │ flow_token: "token123"                                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  Response (respond_to_flow)                                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                   │ │
│  │   "status": 200,                                                    │ │
│  │   "headers": {"Content-Type": "application/json"},                 │ │
│  │   "body": "{\"screen\": \"NEXT_SCREEN\", \"data\": {...}}"        │ │
│  │ }                                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

### 1. Async-First with httpx

**Choice:** httpx over aiohttp or requests

**Rationale:**
- Modern async/await patterns
- Connection pooling built-in
- Full type annotations
- Request/response hooks for customization
- HTTP/2 support

### 2. Pydantic v2 for Types

**Choice:** Pydantic v2 over dataclasses or attrs

**Rationale:**
- Runtime validation
- Automatic serialization/deserialization
- Field aliases (camelCase ↔ snake_case)
- Excellent IDE support
- JSON Schema generation

### 3. Resource-Based API

**Choice:** `client.messages.send_text()` over `client.send_text()`

**Rationale:**
- Mirrors TypeScript SDK design
- Clear namespace organization
- Lazy loading reduces memory
- Easier to extend

### 4. Lazy Resource Loading

**Choice:** Instantiate resources on first access

**Rationale:**
- Minimal memory for unused resources
- Fast client initialization
- Resources share client connection

### 5. Kapso Proxy Detection

**Choice:** Automatic detection from URL

**Rationale:**
- Seamless switching between Meta and Kapso
- No separate client classes needed
- Resources can check and enable features

### 6. Error Hierarchy

**Choice:** Specific exception classes over error codes

**Rationale:**
- Pythonic exception handling
- Type-safe error handling
- Clear retry guidance
- Easy to catch specific errors

### 7. Webhook Normalization

**Choice:** Normalize to flat structure with extensions

**Rationale:**
- Easier to process than nested Meta format
- Consistent camelCase naming
- Direction inference helps routing
- Kapso extension fields in dedicated namespace
