# Usage Examples

Comprehensive examples for using the Kapso WhatsApp Cloud API Python SDK.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Sending Messages](#sending-messages)
- [Media Handling](#media-handling)
- [Interactive Messages](#interactive-messages)
- [Template Messages](#template-messages)
- [Webhooks](#webhooks)
- [Flow Handling](#flow-handling)
- [Error Handling](#error-handling)
- [Framework Integration](#framework-integration)

---

## Basic Setup

### Simple Client Initialization

```python
import asyncio
from kapso_whatsapp import WhatsAppClient

async def main():
    # Using Meta Graph API directly
    client = WhatsAppClient(access_token="your_access_token")

    try:
        response = await client.messages.send_text(
            phone_number_id="123456789",
            to="+15551234567",
            body="Hello!",
        )
        print(f"Sent: {response.message_id}")
    finally:
        await client.close()

asyncio.run(main())
```

### Using Context Manager (Recommended)

```python
import asyncio
from kapso_whatsapp import WhatsAppClient

async def main():
    async with WhatsAppClient(access_token="your_token") as client:
        response = await client.messages.send_text(
            phone_number_id="123456789",
            to="+15551234567",
            body="Hello!",
        )
        print(f"Sent: {response.message_id}")

asyncio.run(main())
```

### Using Kapso Proxy

```python
import asyncio
from kapso_whatsapp import WhatsAppClient

async def main():
    async with WhatsAppClient(
        kapso_api_key="your_kapso_key",
        base_url="https://api.kapso.ai/meta/whatsapp",
    ) as client:
        # All standard API features work
        await client.messages.send_text(...)

        # Plus Kapso-only features
        conversations = await client.conversations.list(
            phone_number_id="123456789",
        )
        print(f"Found {len(conversations.data)} conversations")

asyncio.run(main())
```

### Environment-Based Configuration

```python
import os
from kapso_whatsapp import WhatsAppClient

def create_client() -> WhatsAppClient:
    """Create client from environment variables."""
    if os.getenv("KAPSO_API_KEY"):
        return WhatsAppClient(
            kapso_api_key=os.environ["KAPSO_API_KEY"],
            base_url=os.getenv("KAPSO_BASE_URL", "https://api.kapso.ai/meta/whatsapp"),
        )
    else:
        return WhatsAppClient(
            access_token=os.environ["WHATSAPP_ACCESS_TOKEN"],
        )
```

---

## Sending Messages

### Text Messages

```python
# Simple text
await client.messages.send_text(
    phone_number_id="123456789",
    to="+15551234567",
    body="Hello, World!",
)

# With URL preview
await client.messages.send_text(
    phone_number_id="123456789",
    to="+15551234567",
    body="Check out https://example.com",
    preview_url=True,
)

# Reply to a message
await client.messages.send_text(
    phone_number_id="123456789",
    to="+15551234567",
    body="Thanks for your message!",
    context_message_id="wamid.original_message_id",
)
```

### Location Messages

```python
await client.messages.send_location(
    phone_number_id="123456789",
    to="+15551234567",
    latitude=37.7749,
    longitude=-122.4194,
    name="Salesforce Tower",
    address="415 Mission St, San Francisco, CA",
)
```

### Contact Cards

```python
from kapso_whatsapp import Contact, ContactName, ContactPhone, ContactEmail

await client.messages.send_contacts(
    phone_number_id="123456789",
    to="+15551234567",
    contacts=[
        Contact(
            name=ContactName(
                formattedName="John Doe",
                firstName="John",
                lastName="Doe",
            ),
            phones=[
                ContactPhone(phone="+15559876543", type="MOBILE"),
                ContactPhone(phone="+15551111111", type="WORK"),
            ],
            emails=[
                ContactEmail(email="john@example.com", type="WORK"),
            ],
        ),
    ],
)
```

### Reactions

```python
# Add a reaction
await client.messages.send_reaction(
    phone_number_id="123456789",
    to="+15551234567",
    message_id="wamid.xxx",
    emoji="👍",
)

# Remove a reaction (empty emoji)
await client.messages.send_reaction(
    phone_number_id="123456789",
    to="+15551234567",
    message_id="wamid.xxx",
    emoji="",
)
```

---

## Media Handling

### Upload and Send Image

```python
# Upload an image
with open("photo.jpg", "rb") as f:
    upload_response = await client.media.upload(
        phone_number_id="123456789",
        file=f.read(),
        mime_type="image/jpeg",
        filename="photo.jpg",
    )

# Send using the uploaded media ID
await client.messages.send_image(
    phone_number_id="123456789",
    to="+15551234567",
    image={"id": upload_response.id},
    caption="Here's your photo!",
)
```

### Send Image from URL

```python
await client.messages.send_image(
    phone_number_id="123456789",
    to="+15551234567",
    image={"link": "https://example.com/image.jpg"},
    caption="Image from the web",
)
```

### Send Various Media Types

```python
# Video
await client.messages.send_video(
    phone_number_id="123456789",
    to="+15551234567",
    video={"link": "https://example.com/video.mp4"},
    caption="Check out this video!",
)

# Audio
await client.messages.send_audio(
    phone_number_id="123456789",
    to="+15551234567",
    audio={"link": "https://example.com/audio.mp3"},
)

# Document
await client.messages.send_document(
    phone_number_id="123456789",
    to="+15551234567",
    document={"link": "https://example.com/report.pdf"},
    caption="Monthly report",
    filename="report-2024.pdf",
)

# Sticker
await client.messages.send_sticker(
    phone_number_id="123456789",
    to="+15551234567",
    sticker={"id": "sticker_media_id"},
)
```

### Download Media

```python
# Get media URL
metadata = await client.media.get_url(media_id="media123")
print(f"URL: {metadata.url}")
print(f"MIME: {metadata.mime_type}")
print(f"Size: {metadata.file_size} bytes")

# Download media content
content = await client.media.download(media_id="media123")
with open("downloaded_file", "wb") as f:
    f.write(content)
```

---

## Interactive Messages

### Button Messages

```python
await client.messages.send_interactive_buttons(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="How satisfied are you with our service?",
    buttons=[
        {"id": "satisfied", "title": "Very Satisfied"},
        {"id": "neutral", "title": "Neutral"},
        {"id": "unsatisfied", "title": "Unsatisfied"},
    ],
    header={"type": "text", "text": "Feedback Survey"},
    footer_text="Your feedback helps us improve",
)
```

### List Messages

```python
await client.messages.send_interactive_list(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="Please select your preferred time slot:",
    button_text="View Available Times",
    sections=[
        {
            "title": "Morning",
            "rows": [
                {"id": "9am", "title": "9:00 AM", "description": "Early morning slot"},
                {"id": "10am", "title": "10:00 AM", "description": "Mid-morning slot"},
                {"id": "11am", "title": "11:00 AM", "description": "Late morning slot"},
            ],
        },
        {
            "title": "Afternoon",
            "rows": [
                {"id": "2pm", "title": "2:00 PM", "description": "Early afternoon"},
                {"id": "3pm", "title": "3:00 PM", "description": "Mid-afternoon"},
                {"id": "4pm", "title": "4:00 PM", "description": "Late afternoon"},
            ],
        },
    ],
    header={"type": "text", "text": "Appointment Booking"},
    footer_text="Select your preferred time",
)
```

### CTA URL Button

```python
await client.messages.send_interactive_cta_url(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="Complete your purchase on our website:",
    display_text="Shop Now",
    url="https://shop.example.com/checkout?cart=abc123",
    header={"type": "text", "text": "Complete Your Order"},
    footer_text="Free shipping on orders over $50",
)
```

### Flow Messages

```python
await client.messages.send_interactive_flow(
    phone_number_id="123456789",
    to="+15551234567",
    body_text="Start our customer survey to help us improve",
    flow_id="123456789",
    flow_cta="Start Survey",
    flow_action="navigate",
    flow_action_payload={
        "screen": "WELCOME",
        "data": {"customer_id": "cust123"},
    },
)
```

---

## Template Messages

The `build_template_send_payload` helper assembles the Meta `components` structure from flat per-section lists. Use it instead of hand-rolling `TemplateSendPayload` / `TemplateComponent` / `TemplateParameter`.

### Simple Template

```python
from kapso_whatsapp import TemplateSendPayload

# A bare template with no parameters — direct construction is fine here.
await client.messages.send_template(
    phone_number_id="123456789",
    to="+15551234567",
    template=TemplateSendPayload(name="hello_world", language="en_US"),
)
```

### Template with Body Parameters

```python
from kapso_whatsapp import build_template_send_payload

template = build_template_send_payload(
    name="order_confirmation",
    language="en_US",
    body=[
        {"type": "text", "text": "John"},
        {"type": "text", "text": "ORD-12345"},
        {"type": "text", "text": "$99.99"},
    ],
)
await client.messages.send_template(
    phone_number_id="123456789",
    to="+15551234567",
    template=template,
)
```

### Template with Header Image

```python
from kapso_whatsapp import build_template_send_payload

template = build_template_send_payload(
    name="promotional_offer",
    language="en_US",
    header=[
        {"type": "image", "image": {"link": "https://example.com/promo.jpg"}},
    ],
    body=[
        {"type": "text", "text": "50%"},
        {"type": "text", "text": "SUMMER50"},
    ],
)
await client.messages.send_template(
    phone_number_id="123456789",
    to="+15551234567",
    template=template,
)
```

### Template with Quick Reply Buttons

```python
from kapso_whatsapp import build_template_send_payload

template = build_template_send_payload(
    name="appointment_reminder",
    language="en_US",
    body=[
        {"type": "text", "text": "Dr. Smith"},
        {"type": "text", "text": "Monday, Jan 15 at 2:00 PM"},
    ],
    buttons=[
        {
            "sub_type": "quick_reply",
            "index": 0,
            "parameters": [{"type": "payload", "payload": "confirm_appt"}],
        },
        {
            "sub_type": "quick_reply",
            "index": 1,
            "parameters": [{"type": "payload", "payload": "reschedule_appt"}],
        },
    ],
)
await client.messages.send_template(
    phone_number_id="123456789",
    to="+15551234567",
    template=template,
)
```

### Creating a New Template Definition

When you need to *create* a template (submit it to Meta for approval), use `build_template_definition`:

```python
from kapso_whatsapp import build_template_definition

# Authentication template with a 60s TTL and a copy-code button
auth = build_template_definition(
    name="auth_code",
    category="AUTHENTICATION",
    language="en_US",
    message_send_ttl_seconds=60,
    components=[
        {"type": "BODY", "add_security_recommendation": True},
        {"type": "FOOTER", "code_expiration_minutes": 10},
        {"type": "BUTTONS", "buttons": [{"type": "OTP", "otp_type": "COPY_CODE"}]},
    ],
)
result = await client.templates.create(business_account_id="123456789", **auth)
```

See the [Template Builders reference](api-reference.md#template-builders) for the full catalog of supported component shapes.

---

## Webhooks

### FastAPI Integration

```python
from fastapi import FastAPI, Request, Response, HTTPException
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

app = FastAPI()
APP_SECRET = "your_app_secret"

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Handle Meta webhook verification."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == "your_verify_token":
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhooks."""
    # Verify signature
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=raw_body,
        signature_header=signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process payload
    payload = await request.json()
    result = normalize_webhook(payload)

    # Handle messages
    for message in result.messages:
        msg_type = message.get("type")
        from_number = message.get("from")
        direction = message.get("kapso", {}).get("direction", "inbound")

        if msg_type == "text":
            text = message.get("text", {}).get("body", "")
            print(f"[{direction}] Text from {from_number}: {text}")
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            reply = interactive.get("buttonReply") or interactive.get("listReply")
            if reply:
                print(f"[{direction}] Interactive reply: {reply.get('id')}")

    # Handle status updates
    for status in result.statuses:
        print(f"Message {status.id} is now {status.status}")

    return {"status": "ok"}
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from kapso_whatsapp.webhooks import verify_signature, normalize_webhook

app = Flask(__name__)
APP_SECRET = "your_app_secret"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Handle Meta webhook verification."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == "your_verify_token":
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming webhooks."""
    # Verify signature
    if not verify_signature(
        app_secret=APP_SECRET,
        raw_body=request.data,
        signature_header=request.headers.get("X-Hub-Signature-256"),
    ):
        return "Unauthorized", 401

    # Process payload
    result = normalize_webhook(request.json)

    for message in result.messages:
        print(f"Message from {message.get('from')}: {message.get('type')}")

    return jsonify({"status": "ok"})
```

---

## Flow Handling

### Server-Side Flow Endpoint

```python
import os
from fastapi import FastAPI, Request, Response
from kapso_whatsapp.server import (
    receive_flow_event,
    respond_to_flow,
    FlowReceiveOptions,
    FlowRespondOptions,
)

app = FastAPI()

def get_private_key() -> str:
    """Load private key from environment."""
    return os.environ["FLOW_PRIVATE_KEY"]

@app.post("/flow-endpoint")
async def handle_flow(request: Request):
    """Handle WhatsApp Flow data exchange."""
    raw_body = await request.body()

    # Receive and decrypt flow data
    context = await receive_flow_event(FlowReceiveOptions(
        raw_body=raw_body,
        phone_number_id="123456789",
        get_private_key=get_private_key,
    ))

    print(f"Screen: {context.screen}")
    print(f"Action: {context.action}")
    print(f"Form data: {context.form}")

    # Handle different screens
    if context.screen == "WELCOME":
        response = respond_to_flow(FlowRespondOptions(
            screen="FORM",
            data={
                "title": "Please fill out this form",
                "description": "All fields are required",
            },
        ))
    elif context.screen == "FORM":
        # Process form submission
        name = context.form.get("name", "")
        email = context.form.get("email", "")

        # Save to database...

        response = respond_to_flow(FlowRespondOptions(
            screen="CONFIRMATION",
            data={
                "message": f"Thank you, {name}!",
                "reference_id": "REF-12345",
            },
        ))
    else:
        response = respond_to_flow(FlowRespondOptions(
            error_message="Unknown screen",
        ))

    return Response(
        content=response["body"],
        status_code=response["status"],
        headers=response["headers"],
    )
```

### Handling Flow Media

```python
from kapso_whatsapp.server import download_and_decrypt_media, DownloadMediaOptions

async def process_flow_media(media_info: dict, cdn_url: str):
    """Download and process media from a flow."""
    content = await download_and_decrypt_media(DownloadMediaOptions(
        cdn_url=cdn_url,
        encryption_metadata=media_info.get("encryption_metadata"),
        media_id=media_info.get("id"),
        mime_type=media_info.get("mime_type"),
        phone_number_id="123456789",
        get_private_key=get_private_key,
    ))

    # Save or process the decrypted content
    with open(f"uploads/{media_info['id']}", "wb") as f:
        f.write(content)
```

---

## Error Handling

### Comprehensive Error Handling

```python
from kapso_whatsapp import WhatsAppClient
from kapso_whatsapp.exceptions import (
    WhatsAppAPIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    TimeoutError,
    MessageWindowError,
    KapsoProxyRequiredError,
)

async def send_with_retry(client: WhatsAppClient, phone_id: str, to: str, body: str):
    """Send a message with comprehensive error handling."""
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = await client.messages.send_text(
                phone_number_id=phone_id,
                to=to,
                body=body,
            )
            return response

        except AuthenticationError as e:
            # Token expired or invalid - cannot retry
            print(f"Authentication failed: {e}")
            raise

        except RateLimitError as e:
            # Rate limited - wait and retry
            wait_time = e.retry_after or 60
            print(f"Rate limited. Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
            continue

        except ValidationError as e:
            # Invalid request - cannot retry
            print(f"Validation error: {e}")
            raise

        except MessageWindowError as e:
            # 24-hour window expired - need template
            print(f"Message window expired: {e}")
            raise

        except (NetworkError, TimeoutError) as e:
            # Transient error - can retry
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                print(f"Network error, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            raise

        except KapsoProxyRequiredError as e:
            # Feature requires Kapso proxy
            print(f"Kapso proxy required: {e}")
            raise

        except WhatsAppAPIError as e:
            # Other API error
            print(f"API error {e.code}: {e.message}")
            print(f"Trace ID: {e.fbtrace_id}")
            if e.is_retryable and attempt < max_attempts - 1:
                continue
            raise

    raise Exception("Max retries exceeded")
```

### Logging Errors

```python
import logging
from kapso_whatsapp.exceptions import WhatsAppAPIError, categorize_error, ErrorCategory

logger = logging.getLogger(__name__)

async def send_message_logged(client, **kwargs):
    """Send message with structured logging."""
    try:
        response = await client.messages.send_text(**kwargs)
        logger.info(
            "Message sent",
            extra={
                "message_id": response.message_id,
                "to": kwargs["to"],
            }
        )
        return response

    except WhatsAppAPIError as e:
        category = categorize_error(e)
        logger.error(
            "Message send failed",
            extra={
                "error_code": e.code,
                "error_message": e.message,
                "category": category.value,
                "fbtrace_id": e.fbtrace_id,
                "is_retryable": e.is_retryable,
            },
            exc_info=True,
        )
        raise
```

---

## Framework Integration

### Dependency Injection Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from kapso_whatsapp import WhatsAppClient
import os

# Global client instance
_client: WhatsAppClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage client lifecycle."""
    global _client
    _client = WhatsAppClient(
        access_token=os.environ["WHATSAPP_ACCESS_TOKEN"],
    )
    yield
    await _client.close()

app = FastAPI(lifespan=lifespan)

def get_whatsapp_client() -> WhatsAppClient:
    """Dependency for getting WhatsApp client."""
    if _client is None:
        raise RuntimeError("Client not initialized")
    return _client

@app.post("/send-notification")
async def send_notification(
    to: str,
    message: str,
    client: WhatsAppClient = Depends(get_whatsapp_client),
):
    """Send a notification message."""
    response = await client.messages.send_text(
        phone_number_id=os.environ["PHONE_NUMBER_ID"],
        to=to,
        body=message,
    )
    return {"message_id": response.message_id}
```

### Background Task Pattern

```python
import asyncio
from kapso_whatsapp import WhatsAppClient

class NotificationService:
    """Service for sending notifications in background."""

    def __init__(self, client: WhatsAppClient, phone_number_id: str):
        self.client = client
        self.phone_number_id = phone_number_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the background worker."""
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        """Stop the background worker."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _worker(self):
        """Process notifications from queue."""
        while True:
            to, message = await self.queue.get()
            try:
                await self.client.messages.send_text(
                    phone_number_id=self.phone_number_id,
                    to=to,
                    body=message,
                )
            except Exception as e:
                print(f"Failed to send to {to}: {e}")
            finally:
                self.queue.task_done()

    async def send_async(self, to: str, message: str):
        """Queue a notification for background sending."""
        await self.queue.put((to, message))
```

---

## Kapso Platform API Examples

The following examples use `KapsoPlatformClient` to manage your Kapso project. See [`platform-api.md`](./platform-api.md) for the full reference.

### Onboard a Customer End-to-End

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def onboard_customer(api_key: str, name: str, external_id: str) -> str:
    """Create a customer record and return a setup link URL."""
    async with KapsoPlatformClient(api_key=api_key) as kp:
        customer = await kp.customers.create(
            name=name,
            external_customer_id=external_id,
        )
        link = await kp.setup_links.create(
            customer_id=customer.id,
            success_redirect_url="https://yourapp.com/onboard/done",
            failure_redirect_url="https://yourapp.com/onboard/error",
            language="en",
        )
        return link.url

# Send the returned URL to your customer; they connect their WhatsApp number.
url = asyncio.run(onboard_customer("kp_live_…", "Acme Corp", "cus_acme_001"))
```

### Sync Customers from Your CRM

```python
async def sync_from_crm(api_key: str, crm_customers: list[dict]):
    """Idempotently upsert your CRM customers into Kapso."""
    async with KapsoPlatformClient(api_key=api_key) as kp:
        # Index existing Kapso customers by external_customer_id
        existing = {}
        async for c in kp.customers.iter():
            if c.external_customer_id:
                existing[c.external_customer_id] = c.id

        for crm in crm_customers:
            ext_id = crm["id"]
            if ext_id in existing:
                await kp.customers.update(existing[ext_id], name=crm["name"])
            else:
                await kp.customers.create(name=crm["name"], external_customer_id=ext_id)
```

### Send a Scheduled Broadcast

```python
async def schedule_promo(api_key: str, phone_number_id: str, recipients: list[str]):
    async with KapsoPlatformClient(api_key=api_key) as kp:
        broadcast = await kp.broadcasts.create(
            phone_number_id=phone_number_id,
            name="Spring promo",
            template_name="promo_v3",
            template_language="en_US",
            template_variables={"discount": "20%"},
        )
        await kp.broadcasts.add_recipients(
            broadcast.id,
            recipients=[{"phone": p} for p in recipients],
        )
        await kp.broadcasts.schedule(
            broadcast.id,
            scheduled_at="2026-05-01T15:00:00Z",
        )
        print(f"scheduled broadcast {broadcast.id}")
```

### Query the Kapso-managed Database

```python
async def find_qualified_leads(api_key: str):
    async with KapsoPlatformClient(api_key=api_key) as kp:
        rows = await kp.database.query(
            table="leads",
            where={"status": "qualified"},
            order_by="created_at desc",
            limit=100,
        )
        for row in rows:
            print(row["name"], row["created_at"])
```

### Provision a Webhook and Verify It's Reachable

```python
async def provision_webhook(api_key: str, url: str):
    async with KapsoPlatformClient(api_key=api_key) as kp:
        hook = await kp.project_webhooks.create(
            url=url,
            events=["message.received", "message.delivered", "broadcast.completed"],
            secret_key="whsec_replace_me",
        )
        result = await kp.project_webhooks.test(hook.id, event_type="message.received")
        if not result.success:
            await kp.project_webhooks.delete(hook.id)
            raise RuntimeError(f"webhook {url} did not respond — rolled back")
        print(f"webhook {hook.id} active")
```

### Investigate Failed Webhook Deliveries

```python
async def replay_failed(api_key: str, webhook_id: str):
    """List delivery attempts that didn't get a 2xx response."""
    async with KapsoPlatformClient(api_key=api_key) as kp:
        async for delivery in kp.webhook_deliveries.iter(webhook_id=webhook_id):
            if not (200 <= delivery.response_code < 300):
                print(
                    delivery.attempted_at,
                    delivery.response_code,
                    delivery.event_type,
                )
```

### Mix Both Clients in One Application

A typical pattern: use `KapsoPlatformClient` for project setup, `WhatsAppClient` for live messaging.

```python
import os
from kapso_whatsapp import KapsoPlatformClient, WhatsAppClient

API_KEY = os.environ["KAPSO_API_KEY"]

async def welcome_customer(name: str, phone_number_id: str, to: str):
    async with KapsoPlatformClient(api_key=API_KEY) as kp, \
               WhatsAppClient(kapso_api_key=API_KEY) as wa:
        # Project-management call
        customer = await kp.customers.create(name=name)

        # Messaging call (uses the Kapso Meta-proxy with the same key)
        await wa.messages.send_text(
            phone_number_id=phone_number_id,
            to=to,
            body=f"Welcome, {customer.name}!",
        )
```

### Custom Pagination

```python
# Walk every conversation, but stop once you've seen 500 of them
async with KapsoPlatformClient(api_key=API_KEY) as kp:
    seen = 0
    async for c in kp.conversations.iter(per_page=50):
        process(c)
        seen += 1
        if seen >= 500:
            break

# Or use the generic paginate() for endpoints not yet wrapped as resources
async for row in kp.paginate("custom/path", params={"foo": "bar"}, per_page=100):
    ...
```

### Manage WhatsApp Flow Lifecycle

```python
async def deploy_flow(api_key: str, phone_number_id: str, flow_json: dict):
    async with KapsoPlatformClient(api_key=api_key) as kp:
        flow = await kp.whatsapp_flows.create(
            name="Onboarding",
            phone_number_id=phone_number_id,
            flow_json=flow_json,
        )

        # If your flow has a server-side data endpoint, deploy it
        await kp.whatsapp_flows.upsert_data_endpoint(
            flow.id,
            code=open("flow_handler.js").read(),
        )
        await kp.whatsapp_flows.deploy_data_endpoint(flow.id)
        await kp.whatsapp_flows.register_data_endpoint_with_meta(flow.id)

        # Publish the flow
        await kp.whatsapp_flows.publish(flow.id)

        # Tail logs for the data endpoint
        logs = await kp.whatsapp_flows.get_function_logs(flow.id, limit=100)
        for entry in logs:
            print(entry)
```
