# Webhooks Guide

Complete guide for integrating WhatsApp webhooks with the Kapso WhatsApp Cloud API Python SDK.

## Table of Contents

- [Overview](#overview)
- [Webhook Setup](#webhook-setup)
- [Signature Verification](#signature-verification)
- [Payload Normalization](#payload-normalization)
- [Message Types](#message-types)
- [Status Updates](#status-updates)
- [Direction Inference](#direction-inference)
- [Framework Examples](#framework-examples)
- [Best Practices](#best-practices)

---

## Overview

WhatsApp Cloud API uses webhooks to notify your application about:

- **Incoming messages** - Text, media, location, contacts, interactive responses
- **Message status updates** - Sent, delivered, read, failed
- **Call events** - Incoming/outgoing calls (via Kapso proxy)

```
┌──────────────────┐      ┌─────────────────┐      ┌──────────────────┐
│   WhatsApp       │      │   Meta Cloud    │      │   Your Server    │
│   User           │─────►│   API           │─────►│   /webhook       │
└──────────────────┘      └─────────────────┘      └──────────────────┘
                                                            │
                                                            ▼
                                              ┌──────────────────────────┐
                                              │  1. Verify Signature     │
                                              │  2. Normalize Payload    │
                                              │  3. Process Messages     │
                                              │  4. Handle Statuses      │
                                              └──────────────────────────┘
```

---

## Webhook Setup

### 1. Configure in Meta Developer Console

1. Go to your Meta App Dashboard
2. Navigate to WhatsApp → Configuration
3. Set your webhook URL: `https://your-server.com/webhook`
4. Set a verify token (a secret string you choose)
5. Subscribe to the events you need

### 2. Implement Verification Endpoint

Meta will send a GET request to verify your webhook:

```python
from fastapi import FastAPI, Request, Response, HTTPException

app = FastAPI()
VERIFY_TOKEN = "your_secret_verify_token"

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Handle Meta webhook verification challenge."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # Return the challenge to confirm
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification failed")
```

### 3. Implement Webhook Handler

```python
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

APP_SECRET = "your_app_secret"  # From Meta App Dashboard

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook events."""
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Step 1: Verify signature
    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=raw_body,
        signature_header=signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Step 2: Normalize payload
    payload = await request.json()
    result = normalize_webhook(payload)

    # Step 3: Process messages
    for message in result.messages:
        await process_message(message)

    # Step 4: Handle statuses
    for status in result.statuses:
        await process_status(status)

    return {"status": "ok"}
```

---

## Signature Verification

Always verify webhook signatures to ensure requests come from Meta.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Signature Verification                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Request Header: X-Hub-Signature-256: sha256=abc123...          │
│                                                                  │
│  Your Server:                                                    │
│  1. Extract algorithm and signature from header                  │
│  2. Compute HMAC-SHA256(app_secret, raw_body)                   │
│  3. Compare computed signature with received                     │
│  4. Accept if match, reject if not                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### API Reference

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
| `app_secret` | `str` | Your Meta App Secret |
| `raw_body` | `bytes \| str` | The raw request body (not parsed JSON) |
| `signature_header` | `str \| None` | Value of `X-Hub-Signature-256` header |

**Returns:** `True` if signature is valid, `False` otherwise.

### Example

```python
from kapso_whatsapp.webhooks import verify_signature

# Get values from request
raw_body = await request.body()  # bytes
signature = request.headers.get("X-Hub-Signature-256")

is_valid = verify_signature(
    app_secret="your_app_secret",
    raw_body=raw_body,
    signature_header=signature,
)

if not is_valid:
    return Response(status_code=401)
```

### Security Notes

- **Always use HTTPS** - Webhook URLs must be HTTPS
- **Never log secrets** - Don't log your app secret
- **Verify every request** - Don't skip verification in production
- **Use constant-time comparison** - The SDK uses `hmac.compare_digest`

---

## Payload Normalization

The `normalize_webhook` function transforms Meta's nested webhook structure into a flat, easy-to-use format.

### Why Normalize?

Meta's webhook payload structure is deeply nested:

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {...},
        "messages": [{...}],
        "statuses": [{...}]
      },
      "field": "messages"
    }]
  }]
}
```

After normalization:

```python
result.messages  # List of normalized messages
result.statuses  # List of status updates
result.calls     # List of call events (if any)
```

### API Reference

```python
from kapso_whatsapp.webhooks import normalize_webhook, NormalizedWebhookResult

def normalize_webhook(
    payload: dict | str,
    *,
    business_numbers: list[str] | None = None,
) -> NormalizedWebhookResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `payload` | `dict \| str` | Webhook payload (parsed or JSON string) |
| `business_numbers` | `list[str] \| None` | Your business phone numbers for direction inference |

**Returns:** `NormalizedWebhookResult` with:
- `messages: list[dict]` - Normalized messages
- `statuses: list[WebhookStatus]` - Status updates
- `calls: list[dict]` - Call events

### Normalization Features

1. **Flattens nested structure** - No more digging through `entry[0].changes[0].value`
2. **Converts to camelCase** - Consistent field naming
3. **Merges metadata** - Phone number IDs added to each message
4. **Infers direction** - Determines if message is inbound or outbound
5. **Adds Kapso extensions** - Extra fields in `message.kapso`

---

## Message Types

### Text Messages

```json
{
  "id": "wamid.xxx",
  "from": "15551234567",
  "timestamp": "1234567890",
  "type": "text",
  "text": {
    "body": "Hello, World!"
  },
  "kapso": {
    "direction": "inbound"
  }
}
```

```python
for message in result.messages:
    if message.get("type") == "text":
        text = message["text"]["body"]
        print(f"Received: {text}")
```

### Image Messages

```json
{
  "type": "image",
  "image": {
    "id": "media_id",
    "mimeType": "image/jpeg",
    "sha256": "...",
    "caption": "Optional caption"
  }
}
```

```python
if message.get("type") == "image":
    media_id = message["image"]["id"]
    caption = message["image"].get("caption", "")

    # Download the image
    content = await client.media.download(media_id)
```

### Interactive Responses

**Button Reply:**

```json
{
  "type": "interactive",
  "interactive": {
    "type": "button_reply",
    "buttonReply": {
      "id": "button_id",
      "title": "Button Title"
    }
  }
}
```

**List Reply:**

```json
{
  "type": "interactive",
  "interactive": {
    "type": "list_reply",
    "listReply": {
      "id": "row_id",
      "title": "Row Title",
      "description": "Row description"
    }
  }
}
```

```python
if message.get("type") == "interactive":
    interactive = message["interactive"]
    reply_type = interactive.get("type")

    if reply_type == "button_reply":
        button = interactive["buttonReply"]
        print(f"Button clicked: {button['id']}")

    elif reply_type == "list_reply":
        item = interactive["listReply"]
        print(f"List item selected: {item['id']}")
```

### Location Messages

```json
{
  "type": "location",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "name": "San Francisco",
    "address": "California, USA"
  }
}
```

### Contact Messages

```json
{
  "type": "contacts",
  "contacts": [{
    "name": {
      "formattedName": "John Doe",
      "firstName": "John",
      "lastName": "Doe"
    },
    "phones": [{
      "phone": "+15559876543",
      "type": "MOBILE"
    }]
  }]
}
```

### Order Messages

```json
{
  "type": "order",
  "order": {
    "catalogId": "catalog123",
    "productItems": [{
      "productRetailerId": "product123",
      "quantity": 2,
      "itemPrice": 1999,
      "currency": "USD"
    }]
  }
}
```

---

## Status Updates

Track message delivery status.

### Status Flow

```
┌────────┐    ┌───────────┐    ┌────────┐    ┌────────┐
│  sent  │───►│ delivered │───►│  read  │    │ failed │
└────────┘    └───────────┘    └────────┘    └────────┘
```

### Status Object

```python
class WebhookStatus:
    id: str           # Message ID (wamid.xxx)
    status: str       # sent, delivered, read, failed
    timestamp: str    # Unix timestamp
    recipient_id: str # Recipient phone number

    # Optional error info
    errors: list[WebhookStatusError] | None

    # Conversation info
    conversation: WebhookStatusConversation | None

    # Pricing info
    pricing: WebhookStatusPricing | None
```

### Handling Status Updates

```python
for status in result.statuses:
    msg_id = status.id
    current_status = status.status

    if current_status == "sent":
        print(f"Message {msg_id} sent to server")

    elif current_status == "delivered":
        print(f"Message {msg_id} delivered to device")

    elif current_status == "read":
        print(f"Message {msg_id} was read")

    elif current_status == "failed":
        if status.errors:
            for error in status.errors:
                print(f"Message {msg_id} failed: {error.message}")
                print(f"Error code: {error.code}")
```

### Pricing Information

```python
if status.pricing:
    pricing = status.pricing
    print(f"Pricing model: {pricing.pricing_model}")
    print(f"Category: {pricing.category}")
    # e.g., "marketing", "utility", "authentication"
```

---

## Direction Inference

The SDK automatically infers message direction (inbound vs outbound).

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Direction Inference Logic                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Check for is_echo flag (echo = outbound)                    │
│  2. Check if 'from' matches business number → outbound          │
│  3. Check if 'to' matches business number → inbound             │
│  4. Check context.from for replies → inbound                    │
│  5. Default: if 'from' exists → inbound                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Providing Business Numbers

For more accurate direction inference, provide your business phone numbers:

```python
result = normalize_webhook(
    payload=webhook_data,
    business_numbers=["15551234567", "15559876543"],
)

for message in result.messages:
    direction = message.get("kapso", {}).get("direction")
    print(f"Direction: {direction}")  # "inbound" or "outbound"
```

### Kapso Extension Fields

When using the Kapso proxy, additional fields are populated:

```python
kapso = message.get("kapso", {})

direction = kapso.get("direction")     # "inbound" | "outbound"
flow_response = kapso.get("flowResponse")  # Parsed flow response
flow_token = kapso.get("flowToken")    # Flow token
flow_name = kapso.get("flowName")      # Flow name
order_text = kapso.get("orderText")    # Order description
```

---

## Framework Examples

### FastAPI (Complete Example)

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from kapso_whatsapp import WhatsAppClient
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

# Configuration
APP_SECRET = os.environ["APP_SECRET"]
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]

# Global client
client: WhatsAppClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = WhatsAppClient(access_token=ACCESS_TOKEN)
    yield
    await client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403)

@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=raw_body,
        signature_header=signature,
    ):
        raise HTTPException(status_code=401)

    payload = await request.json()
    result = normalize_webhook(payload, business_numbers=[PHONE_NUMBER_ID])

    for message in result.messages:
        # Only handle inbound messages
        if message.get("kapso", {}).get("direction") != "inbound":
            continue

        if message.get("type") == "text":
            # Echo the message back
            text = message["text"]["body"]
            await client.messages.send_text(
                phone_number_id=PHONE_NUMBER_ID,
                to=message["from"],
                body=f"You said: {text}",
            )

    return {"status": "ok"}
```

### Starlette/Async

```python
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

async def verify_webhook(request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe":
        if params.get("hub.verify_token") == VERIFY_TOKEN:
            return PlainTextResponse(params.get("hub.challenge"))
    return PlainTextResponse("Forbidden", status_code=403)

async def handle_webhook(request):
    body = await request.body()
    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=body,
        signature_header=request.headers.get("x-hub-signature-256"),
    ):
        return PlainTextResponse("Unauthorized", status_code=401)

    result = normalize_webhook(await request.json())
    for msg in result.messages:
        print(f"Message: {msg}")

    return JSONResponse({"status": "ok"})

app = Starlette(routes=[
    Route("/webhook", verify_webhook, methods=["GET"]),
    Route("/webhook", handle_webhook, methods=["POST"]),
])
```

### Django (Async View)

```python
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from asgiref.sync import async_to_sync
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    elif request.method == "POST":
        if not verify_signature(
            app_secret=settings.APP_SECRET,
            raw_body=request.body,
            signature_header=request.headers.get("X-Hub-Signature-256"),
        ):
            return HttpResponse("Unauthorized", status=401)

        payload = json.loads(request.body)
        result = normalize_webhook(payload)

        for message in result.messages:
            # Process message (consider using Celery for async)
            process_message_task.delay(message)

        return JsonResponse({"status": "ok"})
```

---

## Best Practices

### 1. Always Verify Signatures

```python
# Never skip signature verification in production
if not verify_signature(...):
    return 401
```

### 2. Respond Quickly (200 OK)

Meta expects a 200 response within 20 seconds. Process messages asynchronously:

```python
@app.post("/webhook")
async def webhook(request: Request):
    # Verify and normalize...

    # Queue for async processing
    for message in result.messages:
        await message_queue.put(message)

    # Respond immediately
    return {"status": "ok"}
```

### 3. Handle Duplicates

Webhooks may be delivered multiple times. Use message IDs for deduplication:

```python
processed_ids = set()  # Use Redis/DB in production

for message in result.messages:
    msg_id = message.get("id")
    if msg_id in processed_ids:
        continue
    processed_ids.add(msg_id)
    await process_message(message)
```

### 4. Log for Debugging

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()

    # Log the raw payload for debugging
    logger.debug(f"Webhook payload: {json.dumps(payload)}")

    result = normalize_webhook(payload)
    logger.info(f"Received {len(result.messages)} messages")
```

### 5. Handle All Message Types

```python
handlers = {
    "text": handle_text,
    "image": handle_image,
    "video": handle_video,
    "audio": handle_audio,
    "document": handle_document,
    "location": handle_location,
    "contacts": handle_contacts,
    "interactive": handle_interactive,
    "order": handle_order,
    "button": handle_button,
}

for message in result.messages:
    msg_type = message.get("type")
    handler = handlers.get(msg_type)
    if handler:
        await handler(message)
    else:
        logger.warning(f"Unhandled message type: {msg_type}")
```

### 6. Use Proper Error Handling

```python
try:
    result = normalize_webhook(payload)
except Exception as e:
    logger.error(f"Failed to normalize webhook: {e}")
    # Still return 200 to prevent retries
    return {"status": "ok", "error": "processing_failed"}
```
