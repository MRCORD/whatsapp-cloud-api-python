# API Reference

Complete API documentation for the Kapso WhatsApp Cloud API Python SDK.

The SDK ships **two clients**:

- **`WhatsAppClient`** — sends/receives WhatsApp messages via Meta Graph or Kapso's Meta-proxy. Documented below.
- **`KapsoPlatformClient`** — manages your Kapso project (customers, setup links, broadcasts, webhooks, database, integrations, WhatsApp Flow lifecycle). See [`platform-api.md`](./platform-api.md) for the full Platform API reference.

## Table of Contents

- [WhatsAppClient](#whatsappclient)
- [Messages Resource](#messages-resource)
- [Media Resource](#media-resource)
- [Templates Resource](#templates-resource)
- [Flows Resource](#flows-resource)
- [Phone Numbers Resource](#phone-numbers-resource)
- [Conversations Resource](#conversations-resource-kapso-only)
- [Contacts Resource](#contacts-resource-kapso-only)
- [Calls Resource](#calls-resource-kapso-only)
- [Webhooks](#webhooks)
- [Server-Side Flow Handling](#server-side-flow-handling)
- [Template Builders](#template-builders)
- [Types](#types)
- [Exceptions](#exceptions)
- **[Platform API → `platform-api.md`](./platform-api.md)** — `KapsoPlatformClient`, 18 resources, ~87 endpoints

---

## WhatsAppClient

The main client for interacting with the WhatsApp Business Cloud API.

### Constructor

```python
WhatsAppClient(
    access_token: str | None = None,
    kapso_api_key: str | None = None,
    base_url: str = "https://graph.facebook.com",
    graph_version: str = "v23.0",
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_backoff: float = 1.0,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `access_token` | `str \| None` | `None` | Meta Graph API access token |
| `kapso_api_key` | `str \| None` | `None` | Kapso API key (for proxy) |
| `base_url` | `str` | `"https://graph.facebook.com"` | API base URL |
| `graph_version` | `str` | `"v23.0"` | Graph API version |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `retry_backoff` | `float` | `1.0` | Backoff multiplier for retries |

**Note:** You must provide either `access_token` or `kapso_api_key`.

### Methods

#### `is_kapso_proxy() -> bool`

Check if the client is configured to use the Kapso proxy.

```python
client = WhatsAppClient(kapso_api_key="key", base_url="https://api.kapso.ai/meta/whatsapp")
print(client.is_kapso_proxy())  # True
```

#### `close() -> None`

Close the HTTP client connection.

```python
await client.close()
```

### Context Manager

The client supports async context manager protocol:

```python
async with WhatsAppClient(access_token="token") as client:
    await client.messages.send_text(...)
# Connection automatically closed
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `config` | `ClientConfig` | Client configuration |
| `messages` | `MessagesResource` | Messages API resource |
| `media` | `MediaResource` | Media API resource |
| `templates` | `TemplatesResource` | Templates API resource |
| `flows` | `FlowsResource` | Flows API resource |
| `phone_numbers` | `PhoneNumbersResource` | Phone numbers API resource |
| `conversations` | `ConversationsResource` | Conversations (Kapso only) |
| `contacts` | `ContactsResource` | Contacts (Kapso only) |
| `calls` | `CallsResource` | Calls (Kapso only) |

---

## Messages Resource

Send various types of messages via WhatsApp.

### `send_text()`

Send a text message.

```python
async def send_text(
    phone_number_id: str,
    to: str,
    body: str,
    *,
    preview_url: bool = False,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | WhatsApp Business phone number ID |
| `to` | `str` | Yes | Recipient phone number (E.164 format) |
| `body` | `str` | Yes | Message text (max 4096 chars) |
| `preview_url` | `bool` | No | Enable URL preview |
| `context_message_id` | `str` | No | Reply to this message ID |

**Example:**

```python
response = await client.messages.send_text(
    phone_number_id="123456789",
    to="+15551234567",
    body="Hello, World!",
    preview_url=True,
)
print(response.message_id)  # "wamid.xxx"
```

### `send_image()`

Send an image message.

```python
async def send_image(
    phone_number_id: str,
    to: str,
    image: MediaInput | dict,
    *,
    caption: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID |
| `to` | `str` | Yes | Recipient phone number |
| `image` | `MediaInput \| dict` | Yes | Image via `id` or `link` |
| `caption` | `str` | No | Image caption |
| `context_message_id` | `str` | No | Reply to message ID |

**Example:**

```python
# Using a URL
await client.messages.send_image(
    phone_number_id="123456789",
    to="+15551234567",
    image={"link": "https://example.com/image.jpg"},
    caption="Check this out!",
)

# Using a media ID
await client.messages.send_image(
    phone_number_id="123456789",
    to="+15551234567",
    image={"id": "media_id_from_upload"},
)
```

### `send_video()`

Send a video message.

```python
async def send_video(
    phone_number_id: str,
    to: str,
    video: MediaInput | dict,
    *,
    caption: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_audio()`

Send an audio message.

```python
async def send_audio(
    phone_number_id: str,
    to: str,
    audio: MediaInput | dict,
    *,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_document()`

Send a document message.

```python
async def send_document(
    phone_number_id: str,
    to: str,
    document: MediaInput | dict,
    *,
    caption: str | None = None,
    filename: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_sticker()`

Send a sticker message.

```python
async def send_sticker(
    phone_number_id: str,
    to: str,
    sticker: MediaInput | dict,
    *,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_location()`

Send a location message.

```python
async def send_location(
    phone_number_id: str,
    to: str,
    latitude: float,
    longitude: float,
    *,
    name: str | None = None,
    address: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Example:**

```python
await client.messages.send_location(
    phone_number_id="123456789",
    to="+15551234567",
    latitude=37.7749,
    longitude=-122.4194,
    name="San Francisco",
    address="California, USA",
)
```

### `send_contacts()`

Send contact card(s).

```python
async def send_contacts(
    phone_number_id: str,
    to: str,
    contacts: list[Contact],
    *,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Example:**

```python
from kapso_whatsapp import Contact, ContactName, ContactPhone

await client.messages.send_contacts(
    phone_number_id="123456789",
    to="+15551234567",
    contacts=[
        Contact(
            name=ContactName(formattedName="John Doe"),
            phones=[ContactPhone(phone="+15559876543", type="MOBILE")],
        )
    ],
)
```

### `send_template()`

Send a template message.

```python
async def send_template(
    phone_number_id: str,
    to: str,
    template: TemplateSendPayload,
    *,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Example:**

```python
from kapso_whatsapp import TemplateSendPayload, TemplateComponent, TemplateParameter

await client.messages.send_template(
    phone_number_id="123456789",
    to="+15551234567",
    template=TemplateSendPayload(
        name="order_confirmation",
        language="en_US",
        components=[
            TemplateComponent(
                type="body",
                parameters=[
                    TemplateParameter(type="text", text="John"),
                    TemplateParameter(type="text", text="ORD-12345"),
                ],
            ),
        ],
    ),
)
```

### `send_interactive_buttons()`

Send an interactive button message.

```python
async def send_interactive_buttons(
    phone_number_id: str,
    to: str,
    body_text: str,
    buttons: list[Button | dict],
    *,
    header: InteractiveHeader | dict | None = None,
    footer_text: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Example:**

```python
await client.messages.send_interactive_buttons(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="How would you rate our service?",
    buttons=[
        {"id": "great", "title": "Great!"},
        {"id": "ok", "title": "It's OK"},
        {"id": "bad", "title": "Not good"},
    ],
    footer_text="Tap a button to respond",
)
```

### `send_interactive_list()`

Send an interactive list message.

```python
async def send_interactive_list(
    phone_number_id: str,
    to: str,
    body_text: str,
    button_text: str,
    sections: list[ListSection | dict],
    *,
    header: InteractiveHeader | dict | None = None,
    footer_text: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

**Example:**

```python
await client.messages.send_interactive_list(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="Choose from our menu:",
    button_text="View Menu",
    sections=[
        {
            "title": "Drinks",
            "rows": [
                {"id": "coffee", "title": "Coffee", "description": "$3.50"},
                {"id": "tea", "title": "Tea", "description": "$2.50"},
            ],
        },
        {
            "title": "Food",
            "rows": [
                {"id": "sandwich", "title": "Sandwich", "description": "$8.00"},
            ],
        },
    ],
)
```

### `send_interactive_cta_url()`

Send an interactive call-to-action URL button.

```python
async def send_interactive_cta_url(
    phone_number_id: str,
    to: str,
    body_text: str,
    display_text: str,
    url: str,
    *,
    header: InteractiveHeader | dict | None = None,
    footer_text: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_interactive_flow()`

Send an interactive flow message.

```python
async def send_interactive_flow(
    phone_number_id: str,
    to: str,
    body_text: str,
    flow_id: str,
    flow_cta: str,
    *,
    flow_action: str = "navigate",
    flow_action_payload: dict | None = None,
    header: InteractiveHeader | dict | None = None,
    footer_text: str | None = None,
    context_message_id: str | None = None,
) -> SendMessageResponse
```

### `send_reaction()`

Send a reaction to a message.

```python
async def send_reaction(
    phone_number_id: str,
    to: str,
    message_id: str,
    emoji: str,
) -> SendMessageResponse
```

**Example:**

```python
await client.messages.send_reaction(
    phone_number_id="123456789",
    to="+15551234567",
    message_id="wamid.xxx",
    emoji="👍",
)
```

### `mark_as_read()`

Mark a message as read.

```python
async def mark_as_read(
    phone_number_id: str,
    message_id: str,
) -> dict
```

### `query()` (Kapso Only)

Query message history.

```python
async def query(
    phone_number_id: str,
    *,
    wa_id: str | None = None,
    conversation_id: str | None = None,
    fields: str | None = None,
    limit: int = 25,
    after: str | None = None,
    before: str | None = None,
) -> PaginatedResponse[dict]
```

---

## Media Resource

Upload, download, and manage media files.

### `upload()`

Upload a media file.

```python
async def upload(
    phone_number_id: str,
    file: bytes,
    mime_type: str,
    *,
    filename: str | None = None,
) -> MediaUploadResponse
```

**Example:**

```python
with open("image.jpg", "rb") as f:
    response = await client.media.upload(
        phone_number_id="123456789",
        file=f.read(),
        mime_type="image/jpeg",
        filename="photo.jpg",
    )
print(response.id)  # Media ID for sending
```

### `get_url()`

Get the download URL for a media file.

```python
async def get_url(media_id: str) -> MediaMetadata
```

### `download()`

Download a media file.

```python
async def download(
    media_id: str,
    *,
    url: str | None = None,
) -> bytes
```

### `delete()`

Delete a media file.

```python
async def delete(media_id: str) -> dict
```

---

## Templates Resource

Manage message templates.

### `list()`

List all templates.

```python
async def list(
    waba_id: str,
    *,
    name: str | None = None,
    status: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    after: str | None = None,
) -> dict
```

### `get()`

Get a specific template.

```python
async def get(waba_id: str, template_id: str) -> dict
```

### `create()`

Create a new template.

```python
async def create(waba_id: str, template: dict) -> dict
```

### `update()`

Update an existing template.

```python
async def update(waba_id: str, template_id: str, template: dict) -> dict
```

### `delete()`

Delete a template.

```python
async def delete(waba_id: str, name: str, *, hsm_id: str | None = None) -> dict
```

---

## Template Builders

Three top-level helpers for parity with the TS SDK (`@kapso/whatsapp-cloud-api`). All return Pydantic models or dicts that plug into the existing `messages.send_template` and `templates.create` paths. Validation happens at build time so errors surface before the HTTP call.

### `build_template_payload()`

Pass-through validator for raw Meta-style components. Equivalent to `TemplateSendPayload(...)` constructed directly, matched here for TS-SDK migrants.

```python
from kapso_whatsapp import build_template_payload

template = build_template_payload(
    name="order_confirmation",
    language="en_US",  # or {"code": "en_US", "policy": "deterministic"}
    components=[
        {"type": "body", "parameters": [{"type": "text", "text": "Ada"}]},
    ],
)
await client.messages.send_template(
    phone_number_id="123",
    to="+15551234567",
    template=template,
)
```

### `build_template_send_payload()` ← typed shortcut

The ergonomic high-value helper. Pass `body`, `header`, and `buttons` as flat lists; the helper assembles the Meta `components` structure for you.

```python
from kapso_whatsapp import build_template_send_payload

template = build_template_send_payload(
    name="order_confirmation",
    language="en_US",
    body=[
        {"type": "text", "text": "Ada", "parameter_name": "customer_name"},
        {"type": "text", "text": "#1234", "parameter_name": "order_id"},
    ],
    buttons=[
        {
            "sub_type": "flow",
            "index": 0,
            "parameters": [
                {"type": "action", "action": {"flow_token": "FT_123"}},
            ],
        },
    ],
)
```

Accepts `parameterName` (camelCase) as well — Pydantic field aliases handle the conversion. The transport layer normalizes keys to snake_case when sending.

### `build_template_definition()`

Used at template *creation* time (different from sending). Validates the components shape (every component needs a `type`; `BUTTONS` components need a `buttons` array) and returns a dict ready to splat into `templates.create`.

```python
from kapso_whatsapp import build_template_definition

# Authentication template with TTL
auth = build_template_definition(
    name="auth_code",
    language="en_US",
    category="AUTHENTICATION",
    message_send_ttl_seconds=60,
    components=[
        {"type": "BODY", "add_security_recommendation": True},
        {"type": "FOOTER", "code_expiration_minutes": 10},
        {"type": "BUTTONS", "buttons": [{"type": "OTP", "otp_type": "COPY_CODE"}]},
    ],
)
await client.templates.create(business_account_id="123", **auth)

# Named-parameter UTILITY template
named = build_template_definition(
    name="order_confirmation_named",
    language="en_US",
    category="UTILITY",
    parameter_format="NAMED",
    components=[
        {
            "type": "BODY",
            "text": "Thanks {{customer_name}}! Your order {{order_number}} ships {{ship_date}}.",
            "example": {
                "body_text_named_params": [
                    {"param_name": "customer_name", "example": "Ada"},
                    {"param_name": "order_number", "example": "1234"},
                    {"param_name": "ship_date", "example": "2026-05-01"},
                ],
            },
        },
    ],
)
```

---

## Flows Resource

Create and manage WhatsApp Flows.

### `create()`

Create a new flow.

```python
async def create(
    waba_id: str,
    name: str,
    *,
    categories: list[str] | None = None,
    endpoint_uri: str | None = None,
) -> dict
```

### `get()`

Get flow details.

```python
async def get(flow_id: str) -> dict
```

### `update()`

Update a flow.

```python
async def update(flow_id: str, **kwargs) -> dict
```

### `delete()`

Delete a flow.

```python
async def delete(flow_id: str) -> dict
```

### `update_json()`

Update flow JSON definition.

```python
async def update_json(flow_id: str, flow_json: dict | str) -> dict
```

### `get_json()`

Get flow JSON definition.

```python
async def get_json(flow_id: str) -> dict
```

### `publish()`

Publish a flow.

```python
async def publish(flow_id: str) -> dict
```

### `deprecate()`

Deprecate a flow.

```python
async def deprecate(flow_id: str) -> dict
```

---

## Phone Numbers Resource

Manage phone number settings and registration.

### `register()`

Register a phone number.

```python
async def register(
    phone_number_id: str,
    pin: str,
    *,
    data_localization_region: str | None = None,
) -> dict
```

### `deregister()`

Deregister a phone number.

```python
async def deregister(phone_number_id: str) -> dict
```

### `get_business_profile()`

Get business profile.

```python
async def get_business_profile(
    phone_number_id: str,
    *,
    fields: list[str] | None = None,
) -> dict
```

### `update_business_profile()`

Update business profile.

```python
async def update_business_profile(
    phone_number_id: str,
    **profile_fields,
) -> dict
```

### `request_verification_code()`

Request a verification code.

```python
async def request_verification_code(
    phone_number_id: str,
    code_method: Literal["SMS", "VOICE"],
    *,
    language: str = "en",
) -> dict
```

### `verify_code()`

Verify a phone number with code.

```python
async def verify_code(phone_number_id: str, code: str) -> dict
```

---

## Conversations Resource (Kapso Only)

List and manage conversations.

### `list()`

List conversations.

```python
async def list(
    phone_number_id: str,
    *,
    status: str | None = None,
    fields: str | None = None,
    limit: int = 25,
    after: str | None = None,
    before: str | None = None,
) -> PaginatedResponse[Conversation]
```

---

## Contacts Resource (Kapso Only)

Manage contacts.

### `list()`

List contacts.

```python
async def list(
    phone_number_id: str,
    *,
    fields: str | None = None,
    limit: int = 25,
    after: str | None = None,
) -> PaginatedResponse[KapsoContact]
```

### `get()`

Get a specific contact.

```python
async def get(
    phone_number_id: str,
    wa_id: str,
    *,
    fields: str | None = None,
) -> KapsoContact
```

### `update()`

Update a contact.

```python
async def update(
    phone_number_id: str,
    wa_id: str,
    **fields,
) -> KapsoContact
```

---

## Calls Resource (Kapso Only)

Access call logs.

### `list()`

List calls.

```python
async def list(
    phone_number_id: str,
    *,
    wa_id: str | None = None,
    limit: int = 25,
    after: str | None = None,
) -> PaginatedResponse[Call]
```

---

## Webhooks

Utilities for handling WhatsApp webhooks.

### `verify_signature()`

Verify webhook signature.

```python
from kapso_whatsapp.webhooks import verify_signature

def verify_signature(
    *,
    app_secret: str,
    raw_body: bytes | str,
    signature_header: str | None,
) -> bool
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `app_secret` | `str` | Your Meta app secret |
| `raw_body` | `bytes \| str` | Raw request body |
| `signature_header` | `str \| None` | X-Hub-Signature-256 header |

**Example:**

```python
from kapso_whatsapp.webhooks import verify_signature

is_valid = verify_signature(
    app_secret="your_app_secret",
    raw_body=request.body,
    signature_header=request.headers.get("X-Hub-Signature-256"),
)
```

### `normalize_webhook()`

Normalize webhook payload.

```python
from kapso_whatsapp.webhooks import normalize_webhook, NormalizedWebhookResult

def normalize_webhook(
    payload: dict | str,
    *,
    business_numbers: list[str] | None = None,
) -> NormalizedWebhookResult
```

**Returns:** `NormalizedWebhookResult` with:
- `messages: list[dict]` - Normalized messages with direction inference
- `statuses: list[WebhookStatus]` - Message status updates
- `calls: list[dict]` - Call events (if any)

**Example:**

```python
from kapso_whatsapp.webhooks import normalize_webhook

result = normalize_webhook(
    payload=request.json(),
    business_numbers=["15551234567"],
)

for message in result.messages:
    direction = message.get("kapso", {}).get("direction")
    print(f"Message from {message['from']}: {direction}")
```

---

## Server-Side Flow Handling

Handle WhatsApp Flow data exchange on your server.

### `receive_flow_event()`

Receive and decrypt flow data.

```python
from kapso_whatsapp.server import receive_flow_event, FlowReceiveOptions

async def receive_flow_event(options: FlowReceiveOptions) -> FlowContext
```

**FlowReceiveOptions:**

| Field | Type | Description |
|-------|------|-------------|
| `raw_body` | `bytes` | Raw request body |
| `phone_number_id` | `str` | Phone number ID |
| `get_private_key` | `Callable[[], str]` | Function returning private key PEM |

**FlowContext:**

| Field | Type | Description |
|-------|------|-------------|
| `version` | `str` | Flow version |
| `action` | `str` | Flow action |
| `screen` | `str` | Current screen name |
| `form` | `dict` | Form data from user |
| `flow_token` | `str \| None` | Flow token |
| `raw` | `dict` | Raw decrypted payload |

### `respond_to_flow()`

Build a flow response.

```python
from kapso_whatsapp.server import respond_to_flow, FlowRespondOptions

def respond_to_flow(options: FlowRespondOptions) -> dict
```

**FlowRespondOptions:**

| Field | Type | Description |
|-------|------|-------------|
| `screen` | `str` | Next screen to display |
| `data` | `dict` | Data for the screen |
| `flow_token` | `str \| None` | Flow token |
| `error_message` | `str \| None` | Error to display |

**Returns:** `dict` with `status`, `headers`, and `body` for HTTP response.

### `download_and_decrypt_media()`

Download and decrypt media from flows.

```python
from kapso_whatsapp.server import download_and_decrypt_media, DownloadMediaOptions

async def download_and_decrypt_media(options: DownloadMediaOptions) -> bytes
```

---

## Types

### Configuration

```python
from kapso_whatsapp import ClientConfig

class ClientConfig:
    access_token: str | None
    kapso_api_key: str | None
    base_url: str
    graph_version: str
    timeout: float
    max_retries: int
    retry_backoff: float
```

### Message Inputs

```python
from kapso_whatsapp import (
    TextMessageInput,
    MediaInput,
    LocationInput,
    Contact,
    ContactName,
    Button,
    ListSection,
    ListRow,
    TemplateComponent,
    TemplateParameter,
    TemplateSendPayload,
)
```

### Responses

```python
from kapso_whatsapp import (
    SendMessageResponse,
    MediaUploadResponse,
    MediaMetadata,
)
```

### Enums

```python
from kapso_whatsapp import (
    MessageType,      # text, image, video, audio, document, etc.
    MessageStatus,    # sent, delivered, read, failed
    MessageDirection, # inbound, outbound
)
```

---

## Exceptions

All exceptions inherit from `WhatsAppAPIError`.

```python
from kapso_whatsapp.exceptions import (
    WhatsAppAPIError,        # Base exception
    AuthenticationError,     # 401 - Invalid token
    RateLimitError,          # 429 - Rate limit exceeded
    ValidationError,         # 400 - Invalid parameters
    NetworkError,            # Connection failures
    TimeoutError,            # Request timeout
    MessageWindowError,      # 24-hour window expired
    KapsoProxyRequiredError, # Feature requires Kapso proxy
)
```

### Exception Properties

```python
class WhatsAppAPIError(Exception):
    message: str           # Error message
    code: int | None       # Error code
    subcode: int | None    # Error subcode
    fbtrace_id: str | None # Facebook trace ID
    http_status: int | None # HTTP status code
    is_retryable: bool     # Whether to retry
    retry_action: RetryAction # Retry guidance

class RateLimitError(WhatsAppAPIError):
    retry_after: float | None  # Seconds to wait
```

### Error Categorization

```python
from kapso_whatsapp.exceptions import categorize_error, ErrorCategory

category = categorize_error(error)
# Returns: ErrorCategory.AUTHENTICATION, RATE_LIMIT, VALIDATION, etc.
```
