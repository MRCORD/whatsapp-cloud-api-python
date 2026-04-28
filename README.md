# Kapso WhatsApp Cloud API - Python SDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/kapso-whatsapp-cloud-api.svg)](https://pypi.org/project/kapso-whatsapp-cloud-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-340%20passed-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

A modern, async Python client for the WhatsApp Business Cloud API with Pydantic validation and Kapso proxy support.

The package ships **two clients**:

- `WhatsAppClient` — send/receive WhatsApp messages via Meta Graph or the Kapso Meta-proxy.
- `KapsoPlatformClient` — manage your Kapso project itself: customers, setup links, broadcasts, webhooks, the Kapso-managed database, integrations, WhatsApp Flow lifecycle, and more.

## ✨ Features

- **Full WhatsApp Cloud API Support**: Messages, templates, media, flows, and more
- **Kapso Platform API**: 18 resources (customers, setup links, broadcasts, webhooks, database, integrations, WhatsApp Flows, …) covering the full Platform API surface
- **Template Builders**: `build_template_send_payload`, `build_template_payload`, and `build_template_definition` for compose-time validation (TS SDK parity)
- **Async/Await**: Built on httpx for efficient async HTTP operations
- **Type Safety**: Pydantic v2 models for request/response validation
- **Retry Logic**: Automatic retries with exponential backoff for transient errors
- **Kapso Proxy Integration**: Optional enhanced features via Kapso proxy
- **Webhook Handling**: Signature verification and payload normalization
- **Flow Server Support**: Handle WhatsApp Flow data exchange server-side

## 📦 Installation

```bash
pip install kapso-whatsapp-cloud-api
```

Or with uv:

```bash
uv add kapso-whatsapp-cloud-api
```

## 🚀 Quick Start

### Sending Messages

```python
from kapso_whatsapp import WhatsAppClient

async def main():
    async with WhatsAppClient(access_token="your_token") as client:
        # Send a text message
        response = await client.messages.send_text(
            phone_number_id="123456789",
            to="+15551234567",
            body="Hello from Python!",
        )
        print(f"Message sent: {response.message_id}")

        # Send an image
        await client.messages.send_image(
            phone_number_id="123456789",
            to="+15551234567",
            image={"link": "https://example.com/image.jpg"},
            caption="Check this out!",
        )

        # Send interactive buttons
        await client.messages.send_interactive_buttons(
            phone_number_id="123456789",
            to="+15551234567",
            body_text="Choose an option:",
            buttons=[
                {"id": "opt1", "title": "Option 1"},
                {"id": "opt2", "title": "Option 2"},
            ],
        )
```

### Using with Kapso Proxy

```python
from kapso_whatsapp import WhatsAppClient

async with WhatsAppClient(
    kapso_api_key="your_kapso_key",
    base_url="https://api.kapso.ai/meta/whatsapp",
) as client:
    # Access Kapso-specific features
    conversations = await client.conversations.list(
        phone_number_id="123456789",
        status="active",
    )

    # Query message history
    messages = await client.messages.query(
        phone_number_id="123456789",
        wa_id="15551234567",
    )
```

### Webhook Handling

```python
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

# Verify webhook signature
is_valid = verify_signature(
    app_secret="your_app_secret",
    raw_body=request.body,
    signature_header=request.headers.get("X-Hub-Signature-256"),
)

if not is_valid:
    return Response(status_code=401)

# Normalize webhook payload
result = normalize_webhook(request.json())

for message in result.messages:
    print(f"From: {message.get('from')}")
    print(f"Type: {message.get('type')}")
    print(f"Direction: {message.get('kapso', {}).get('direction')}")

for status in result.statuses:
    print(f"Message {status.id} is {status.status}")
```

### Template Messages

The `build_template_send_payload` helper assembles the Meta `components` structure from flat per-section lists — much less error-prone than hand-rolling the nested shape:

```python
from kapso_whatsapp import WhatsAppClient, build_template_send_payload

async with WhatsAppClient(access_token="token") as client:
    template = build_template_send_payload(
        name="order_confirmation",
        language="en_US",
        body=[
            {"type": "text", "text": "John"},
            {"type": "text", "text": "ORD-12345"},
        ],
    )
    await client.messages.send_template(
        phone_number_id="123456789",
        to="+15551234567",
        template=template,
    )
```

For raw Meta-style components, use `build_template_payload`. For creating new template definitions (and submitting to Meta for approval), use `build_template_definition`. See the [Template Builders reference](docs/api-reference.md#template-builders).

### Flow Server-Side Handling

```python
from kapso_whatsapp.server import (
    receive_flow_event,
    respond_to_flow,
    FlowReceiveOptions,
    FlowRespondOptions,
)

async def handle_flow_request(request):
    # Receive and decrypt flow data
    context = await receive_flow_event(FlowReceiveOptions(
        raw_body=request.body,
        phone_number_id="123456789",
        get_private_key=lambda: os.environ["FLOW_PRIVATE_KEY"],
    ))

    print(f"Screen: {context.screen}")
    print(f"Form data: {context.form}")

    # Respond with next screen
    response = respond_to_flow(FlowRespondOptions(
        screen="CONFIRMATION",
        data={"order_id": "12345", "total": 99.99},
    ))

    return Response(
        content=response["body"],
        status_code=response["status"],
        headers=response["headers"],
    )
```

## 📚 Resources

`WhatsAppClient` (messaging via Meta Graph or Kapso Meta-proxy):

| Resource | Description |
|----------|-------------|
| `client.messages` | Send text, media, templates, interactive messages |
| `client.media` | Upload, download, and manage media files |
| `client.templates` | Manage message templates |
| `client.flows` | Create, publish, and manage WhatsApp Flows |
| `client.phone_numbers` | Manage phone number settings and business profile |
| `client.conversations` | List conversations (Kapso proxy only) |
| `client.contacts` | Manage contacts (Kapso proxy only) |
| `client.calls` | Call logs and operations (Kapso proxy only) |

## 🛠 Kapso Platform API

`KapsoPlatformClient` manages your Kapso project itself — separate from messaging:

```python
from kapso_whatsapp import KapsoPlatformClient

async with KapsoPlatformClient(api_key="kp_live_…") as kp:
    # Onboard a customer and generate a setup link
    customer = await kp.customers.create(name="Acme Corp", external_customer_id="cus_42")
    setup = await kp.setup_links.create(customer_id=customer.id)
    print(setup.url)

    # Iterate every broadcast across pages
    async for broadcast in kp.broadcasts.iter():
        print(broadcast.name)

    # Query the Kapso-managed database
    rows = await kp.database.query(table="leads", where={"status": "qualified"})
```

| Resource | Endpoints |
|----------|-----------|
| `kp.customers` | list / iter / get / create / update / delete |
| `kp.setup_links` | list / create / update |
| `kp.phone_numbers` | list / connect / get / update / delete / `check_health` |
| `kp.display_names` | list / submit / retrieve |
| `kp.users` | list project users |
| `kp.broadcasts` | list / iter / get / create / recipients (list/iter/add) / send / schedule / cancel |
| `kp.messages` | list / get |
| `kp.conversations` | list / get / update_status / assignments (CRUD) |
| `kp.contacts` | list / iter / get / create / update / erase |
| `kp.media` | upload |
| `kp.project_webhooks` | list / get / create / update / delete / test |
| `kp.webhooks` | list / get / create / update / delete |
| `kp.webhook_deliveries` | list / iter |
| `kp.api_logs` | list / iter |
| `kp.database` | query / get / insert / upsert / update / delete |
| `kp.integrations` | CRUD + apps / actions / accounts / connect tokens / action schemas |
| `kp.provider_models` | list |
| `kp.whatsapp_flows` | flows + versions + data endpoint lifecycle + function logs/invocations |

Configuration:

- Base URL: `https://api.kapso.ai/platform/v1` (override via `base_url=` for staging).
- Auth: `X-API-Key` header (project API key).
- Pagination: `?page=N&per_page=N`. Every paginated `list(...)` has a matching `iter(...)` async generator that walks all pages.
- Errors: same exception hierarchy as `WhatsAppClient` (`AuthenticationError`, `RateLimitError`, `NotFoundError`, etc.) — `retry_after` honored on 429.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsAppClient                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Config    │  │   httpx     │  │     Retry Logic         │  │
│  │  (Pydantic) │  │AsyncClient  │  │  (exponential backoff)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Messages    │    │    Media      │    │   Templates   │
│   Resource    │    │   Resource    │    │   Resource    │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ • send_text   │    │ • upload      │    │ • create      │
│ • send_image  │    │ • download    │    │ • list        │
│ • send_video  │    │ • get_url     │    │ • get         │
│ • send_audio  │    │ • delete      │    │ • update      │
│ • send_doc    │    └───────────────┘    │ • delete      │
│ • send_tmpl   │                         └───────────────┘
│ • interactive │
└───────────────┘
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    Flows      │    │ PhoneNumbers  │    │  Kapso Only   │
│   Resource    │    │   Resource    │    │   Resources   │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ • create      │    │ • register    │    │ Conversations │
│ • get         │    │ • get_profile │    │ Contacts      │
│ • update      │    │ • set_profile │    │ Calls         │
│ • deploy      │    │ • get_code    │    └───────────────┘
│ • publish     │    │ • verify_code │
└───────────────┘    └───────────────┘
```

## ⚠️ Error Handling

```python
from kapso_whatsapp import WhatsAppClient
from kapso_whatsapp.exceptions import (
    WhatsAppAPIError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
)

try:
    async with WhatsAppClient(access_token="token") as client:
        await client.messages.send_text(...)
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except ValidationError as e:
    print(f"Invalid request: {e}")
except WhatsAppAPIError as e:
    print(f"API error {e.code}: {e.message}")
```

### Error Hierarchy

```
WhatsAppAPIError (base)
├── AuthenticationError     # 401, invalid tokens
├── RateLimitError          # 429, rate limits (has retry_after)
├── ValidationError         # 400, invalid parameters
├── NetworkError            # Connection failures
├── TimeoutError            # Request timeouts
├── MessageWindowError      # 24h window expired
└── KapsoProxyRequiredError # Kapso-only feature attempted
```

## ⚙️ Configuration

```python
client = WhatsAppClient(
    access_token="your_token",        # Meta access token
    # OR
    kapso_api_key="your_key",                      # Kapso API key
    base_url="https://api.kapso.ai/meta/whatsapp", # Kapso proxy URL

    # Optional configuration
    graph_version="v23.0",            # Graph API version
    timeout=30.0,                     # Request timeout (seconds)
    max_retries=3,                    # Max retry attempts
    retry_backoff=1.0,                # Retry backoff multiplier
)
```

## 📖 Documentation

### Reference

- **[API Reference](docs/api-reference.md)** — `WhatsAppClient` API + Template Builders
- **[Platform API Reference](docs/platform-api.md)** — `KapsoPlatformClient`: 18 resources, ~87 endpoints
- **[Examples](docs/examples.md)** — runnable usage examples for both clients
- **[Webhooks Guide](docs/webhooks.md)** — signature verification + payload normalization
- **[Architecture](docs/architecture.md)** — two-client topology, shared `_HttpCore`, diagrams

### Cookbooks

- **[Database Cookbook](docs/cookbook-database.md)** — idempotent upsert, query composition, schema-light migrations, pagination patterns
- **[Integrations Cookbook](docs/cookbook-integrations.md)** — OAuth connect-token flow, app/action discovery, action prop configuration

### Project

- **[Changelog](CHANGELOG.md)** — version history
- **[Deprecation Policy](docs/deprecation-policy.md)** — semver guarantees, breaking-change rules, deprecation timeline
- **[Contributing](CONTRIBUTING.md)** — dev setup, testing, PR conventions

## 🧪 Development

```bash
# Clone the repository
git clone https://github.com/gokapso/whatsapp-cloud-api-python.git
cd whatsapp-cloud-api-python

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src
```

## 📋 Requirements

- Python 3.10+
- httpx >= 0.27.0
- pydantic >= 2.0.0
- cryptography >= 42.0.0 (for Flow encryption)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- [Documentation](https://docs.kapso.ai/docs/whatsapp/python-sdk)
- [WhatsApp Cloud API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Kapso Platform](https://kapso.ai)
- [GitHub Issues](https://github.com/gokapso/whatsapp-cloud-api-python/issues)
