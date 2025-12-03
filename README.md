# Kapso WhatsApp Cloud API - Python SDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/kapso-whatsapp-cloud-api.svg)](https://pypi.org/project/kapso-whatsapp-cloud-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

A modern, async Python client for the WhatsApp Business Cloud API with Pydantic validation and Kapso proxy support.

## ✨ Features

- **Full WhatsApp Cloud API Support**: Messages, templates, media, flows, and more
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
    base_url="https://api.kapso.ai",
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

```python
from kapso_whatsapp import (
    WhatsAppClient,
    TemplateSendPayload,
    TemplateComponent,
    TemplateParameter,
)

async with WhatsAppClient(access_token="token") as client:
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

The client provides access to various WhatsApp API resources:

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
    kapso_api_key="your_key",         # Kapso API key
    base_url="https://api.kapso.ai",  # Kapso proxy URL

    # Optional configuration
    graph_version="v23.0",            # Graph API version
    timeout=30.0,                     # Request timeout (seconds)
    max_retries=3,                    # Max retry attempts
    retry_backoff=1.0,                # Retry backoff multiplier
)
```

## 📖 Documentation

- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Examples](docs/examples.md)** - Detailed usage examples
- **[Webhooks Guide](docs/webhooks.md)** - Webhook integration
- **[Architecture](docs/architecture.md)** - System design and diagrams

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
