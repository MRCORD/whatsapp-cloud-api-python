# Kapso Platform API Reference

`KapsoPlatformClient` is the SDK's client for the **Kapso Platform API** at `https://api.kapso.ai/platform/v1`. It manages your Kapso project itself — customers, setup links, broadcasts, webhooks, the Kapso-managed database, integrations, WhatsApp Flow lifecycle — and is **separate from `WhatsAppClient`**, which sends/receives WhatsApp messages.

Both clients share an internal HTTP transport (connection pool, retry-with-backoff, error categorization), so retry semantics and the exception hierarchy are identical across them.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Response Envelope and Pagination](#response-envelope-and-pagination)
- [Errors and Rate Limits](#errors-and-rate-limits)
- [Resources](#resources)
  - [Customers](#customers)
  - [Setup Links](#setup-links)
  - [Phone Numbers](#phone-numbers)
  - [Display Names](#display-names)
  - [Users](#users)
  - [Broadcasts](#broadcasts)
  - [Messages](#messages)
  - [Conversations](#conversations)
  - [Contacts](#contacts)
  - [Media](#media)
  - [Project Webhooks](#project-webhooks)
  - [Webhooks](#webhooks-phone-number-scoped)
  - [Webhook Deliveries](#webhook-deliveries)
  - [API Logs](#api-logs)
  - [Provider Models](#provider-models)
  - [Database](#database)
  - [Integrations](#integrations)
  - [WhatsApp Flows](#whatsapp-flows)
- [Advanced Usage](#advanced-usage)

## Quick Start

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def main():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        # 1. Create a customer
        customer = await kp.customers.create(
            name="Acme Corp",
            external_customer_id="cus_acme_001",
        )

        # 2. Generate a setup link they can use to connect WhatsApp
        link = await kp.setup_links.create(customer_id=customer.id)
        print(f"send the customer this URL: {link.url}")

        # 3. Iterate every customer in your project (auto-paginates)
        async for c in kp.customers.iter():
            print(c.name)

asyncio.run(main())
```

## Configuration

```python
KapsoPlatformClient(
    api_key: str,                # required — your Kapso project API key
    base_url: str = "https://api.kapso.ai/platform/v1",
    timeout: float = 30.0,       # per-request timeout, seconds
    max_retries: int = 3,        # retries on retryable errors (429, 5xx, network)
    retry_backoff: float = 1.0,  # exponential backoff multiplier
)
```

The client is async-only and supports `async with` for lifecycle management:

```python
async with KapsoPlatformClient(api_key="…") as kp:
    ...
# client.close() is called automatically on exit
```

To pin to a non-production base URL (e.g. staging), pass `base_url=`. The trailing slash is stripped.

## Authentication

Authentication is via the `X-API-Key` header, set automatically from the `api_key` constructor argument. No Bearer token, no OAuth, no per-request auth juggling.

The same Kapso project API key works for both `KapsoPlatformClient` (Platform API) and `WhatsAppClient(kapso_api_key=…)` (Meta-proxied messaging).

## Response Envelope and Pagination

Every Platform endpoint returns the same envelope:

```json
{
  "data": {...},
  "meta": {"page": 1, "per_page": 20, "total_pages": 1, "total_count": 0}
}
```

The SDK exposes three ways to consume this:

### Resource methods (recommended)

Each resource provides typed methods that return Pydantic models with `data` already unwrapped:

```python
customer = await kp.customers.get("uuid-…")          # returns Customer
customers = await kp.customers.list(per_page=50)     # returns list[Customer]
async for c in kp.customers.iter():                  # async generator over all pages
    ...
```

### `client.request()` — unwrapped data

For paths the SDK doesn't yet wrap, or when you want raw dicts:

```python
data = await kp.request("GET", "customers/abc")     # returns the inner data dict
rows = await kp.request("GET", "customers")          # returns the inner data list
```

### `client.request_raw()` — full envelope

When you need pagination metadata or are implementing your own iterator:

```python
envelope = await kp.request_raw("GET", "customers", params={"page": 2})
print(envelope["meta"]["total_pages"])
for row in envelope["data"]:
    ...
```

### `client.paginate()` — generic iterator

Walks all pages of any list endpoint:

```python
async for row in kp.paginate("customers", params={"name_contains": "acme"}, per_page=50):
    print(row["name"])
```

The paginator accepts both `meta.page` (the standard) and `meta.current_page` (used by some endpoints) so you don't need to special-case.

## Errors and Rate Limits

`KapsoPlatformClient` raises the same exception hierarchy as `WhatsAppClient`:

| Status | Exception | Retryable |
|--------|-----------|-----------|
| 401 | `AuthenticationError` | No |
| 403 | `AuthorizationError` | No |
| 404 | `NotFoundError` | No |
| 400 / 422 | `ValidationError` | No |
| 429 | `RateLimitError` | Yes (honors `Retry-After`) |
| 5xx | `WhatsAppAPIError` | Yes (exponential backoff) |
| connect / timeout | `NetworkError` / `TimeoutError` | Yes |

```python
from kapso_whatsapp import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    KapsoPlatformClient,
)

async with KapsoPlatformClient(api_key="…") as kp:
    try:
        customer = await kp.customers.get("does-not-exist")
    except NotFoundError:
        ...
    except RateLimitError as e:
        # 429: e.retry_after is the seconds the API asked us to wait
        print(f"throttled, retry in {e.retry_after}s")
```

Rate limit headers (`X-RateLimit-*`, `X-Burst-RateLimit-*` for workflow executions) are read by the transport layer; the configured `max_retries` will automatically wait the `Retry-After` interval before retrying.

## Resources

Every resource hangs off the client as a lazy-loaded property. You don't need to instantiate them yourself.

### Customers

Customers are the tenants you onboard onto your Kapso project.

```python
# CRUD
customer = await kp.customers.create(name="Acme", external_customer_id="cus_42")
customer = await kp.customers.get("uuid-…")
customer = await kp.customers.update("uuid-…", name="Acme Inc.")
await kp.customers.delete("uuid-…")

# List with filters (single page)
results = await kp.customers.list(
    name_contains="acme",
    external_customer_id="cus_42",
    created_after="2026-01-01T00:00:00Z",
    created_before="2026-12-31T23:59:59Z",
    per_page=50,
    page=1,
)

# Iterate every customer matching the filters (auto-paginates)
async for c in kp.customers.iter(name_contains="acme"):
    print(c.id, c.name)
```

### Setup Links

Setup links let your customer connect their own WhatsApp number to your Kapso project.

```python
# Create a setup link for a customer
link = await kp.setup_links.create(
    customer_id="uuid-of-customer",
    success_redirect_url="https://yourapp.com/onboard/done",
    failure_redirect_url="https://yourapp.com/onboard/error",
    allowed_connection_types=["meta_provided", "embedded_signup"],
    provision_phone_number=False,
    language="en",
)
print(link.url)  # send this to your customer

# List a customer's setup links
links = await kp.setup_links.list(customer_id="uuid-…")

# Update an existing link's redirect URLs
await kp.setup_links.update(
    "uuid-of-link",
    success_redirect_url="https://yourapp.com/v2/onboard/done",
)
```

### Phone Numbers

WhatsApp phone numbers connected to your project.

```python
# List
phones = await kp.phone_numbers.list()

# Get / update / delete
phone = await kp.phone_numbers.get("uuid-…")
await kp.phone_numbers.update("uuid-…", display_name="Acme Support")
await kp.phone_numbers.delete("uuid-…")

# Connect a new phone number (typically called by your backend after Meta OAuth)
phone = await kp.phone_numbers.connect(...)

# Health check — returns connection status, throughput, quality rating
health = await kp.phone_numbers.check_health("uuid-…")
```

### Display Names

WhatsApp Business display name change requests (must be approved by Meta).

```python
# List requests for a phone number
requests = await kp.display_names.list(phone_number_id="uuid-…")

# Submit a new request
req = await kp.display_names.submit(
    phone_number_id="uuid-…",
    requested_display_name="Acme Support",
)

# Check the status of a specific request
req = await kp.display_names.retrieve(phone_number_id="uuid-…", request_id="…")
```

### Users

Users who are members of your Kapso project.

```python
users = await kp.users.list()
async for u in kp.users.iter():
    print(u.email, u.role)
```

> Note: the published doc shows `id` as an integer placeholder (`1`), but the live API returns UUID strings. The SDK's `ProjectUser.id` is typed `str` to match the live shape.

### Broadcasts

Bulk messaging campaigns.

```python
# Create a broadcast
broadcast = await kp.broadcasts.create(
    phone_number_id="uuid-…",
    name="February promo",
    template_name="promo_v3",
    template_language="en_US",
    template_variables={"discount": "20%"},
)

# Add recipients
await kp.broadcasts.add_recipients(
    broadcast.id,
    recipients=[{"phone": "+15551234567"}, {"phone": "+15559876543"}],
)

# Or list / iterate recipients on an existing broadcast
recipients = await kp.broadcasts.list_recipients(broadcast.id)
async for r in kp.broadcasts.iter_recipients(broadcast.id):
    ...

# Send now
await kp.broadcasts.send(broadcast.id)

# Or schedule
await kp.broadcasts.schedule(broadcast.id, scheduled_at="2026-05-01T10:00:00Z")

# Cancel a scheduled broadcast
await kp.broadcasts.cancel(broadcast.id)

# List / get / iterate
broadcasts = await kp.broadcasts.list(per_page=20)
async for b in kp.broadcasts.iter():
    ...
b = await kp.broadcasts.get("uuid-…")
```

### Messages

Read-only access to the message history for a project.

```python
messages = await kp.messages.list(per_page=50, conversation_id="uuid-…")
m = await kp.messages.get("uuid-…")
```

### Conversations

```python
# List / get / iterate
conversations = await kp.conversations.list(per_page=20, status="open")
c = await kp.conversations.get("uuid-…")
async for c in kp.conversations.iter(status="open"):
    ...

# Update status (open / closed / spam)
await kp.conversations.update_status("uuid-…", status="closed")

# Conversation assignments (assigning agents to a conversation)
assignments = await kp.conversations.list_assignments("uuid-conversation")
a = await kp.conversations.create_assignment(
    "uuid-conversation",
    assignee_id="uuid-user",
)
a = await kp.conversations.get_assignment("uuid-conversation", "uuid-assignment")
await kp.conversations.update_assignment(
    "uuid-conversation",
    "uuid-assignment",
    status="resolved",
)
```

### Contacts

```python
contacts = await kp.contacts.list(per_page=50, search="acme")
async for c in kp.contacts.iter():
    ...

c = await kp.contacts.create(phone="+15551234567", name="Alice")
c = await kp.contacts.get("uuid-…")
c = await kp.contacts.update("uuid-…", name="Alice Smith")

# GDPR-style erasure
await kp.contacts.erase("uuid-…")
```

### Media

```python
# Upload media (returns the media id usable in send_template etc.)
with open("logo.png", "rb") as f:
    upload = await kp.media.upload(file=f, mime_type="image/png")
print(upload.id)
```

### Project Webhooks

Project-level webhooks that receive events for the entire Kapso project.

```python
# CRUD
hook = await kp.project_webhooks.create(
    url="https://yourapp.com/kapso-events",
    events=["message.received", "message.delivered"],
    secret_key="whsec_…",
)
hooks = await kp.project_webhooks.list()
async for h in kp.project_webhooks.iter():
    ...
hook = await kp.project_webhooks.get("uuid-…")
hook = await kp.project_webhooks.update("uuid-…", events=["message.received"])
await kp.project_webhooks.delete("uuid-…")

# Send a test payload to verify the endpoint
result = await kp.project_webhooks.test("uuid-…", event_type="message.received")
print(result.success)
```

### Webhooks (phone-number-scoped)

Phone-number-scoped webhooks, distinct from project webhooks.

```python
phone_id = "uuid-of-phone-number"

hooks = await kp.webhooks.list(phone_id)
async for h in kp.webhooks.iter(phone_id):
    ...

hook = await kp.webhooks.create(
    phone_id,
    url="https://yourapp.com/wa-events",
    events=["message.received"],
)
hook = await kp.webhooks.get(phone_id, "uuid-hook")
hook = await kp.webhooks.update(phone_id, "uuid-hook", active=False)
await kp.webhooks.delete(phone_id, "uuid-hook")
```

### Webhook Deliveries

Inspect individual webhook delivery attempts (debugging).

```python
deliveries = await kp.webhook_deliveries.list(webhook_id="uuid-…", per_page=50)
async for d in kp.webhook_deliveries.iter(webhook_id="uuid-…"):
    print(d.status, d.response_code, d.attempted_at)
```

### API Logs

Audit log of API calls made against your project.

```python
logs = await kp.api_logs.list(per_page=50)
async for entry in kp.api_logs.iter():
    print(entry.method, entry.path, entry.status_code)
```

### Provider Models

LLM provider/model catalog supported by Kapso (used in agent/workflow config).

```python
models = await kp.provider_models.list()
for m in models:
    print(m.provider, m.model, m.context_window)
```

(This endpoint is not paginated — `list()` returns everything; there is no `iter()`.)

### Database

The Kapso-managed database for storing application state.

```python
# Query rows with PostgREST-style filters (status="eq.qualified", etc.)
rows = await kp.database.query(
    "leads",
    select="id,name,status",
    order="created_at.desc",
    limit=100,
    status="eq.qualified",
)

# Get a single row by primary key
row = await kp.database.get("leads", "lead-123")

# Insert one or many
await kp.database.insert("leads", [{"name": "Alice", "status": "new"}])

# Upsert (PUT semantics; conflict resolution is on the table's primary key,
# no caller-controlled on_conflict column)
await kp.database.upsert(
    "leads",
    [{"id": "lead-123", "status": "qualified"}],
)

# Update — `fields` is a positional dict; filters are kwargs
await kp.database.update(
    "leads",
    {"status": "contacted"},
    status="eq.new",
)

# Delete with filters
await kp.database.delete("leads", status="eq.spam")
```

> See [`docs/cookbook-database.md`](./cookbook-database.md) for in-depth patterns: idempotent upsert, schema-light migrations, query composition, pagination, and error handling.

### Integrations

Third-party integrations (Stripe, HubSpot, Slack, etc.) connected via Pipedream.

```python
# Discover what's available — search the Pipedream app catalog
apps = await kp.integrations.list_apps(query="stripe", has_actions=True)
actions = await kp.integrations.list_actions(app_slug="stripe")

# CRUD on saved integrations in your project
integrations = await kp.integrations.list()
intg = await kp.integrations.create(
    action_id="stripe-create-customer",
    app_slug="stripe",
    name="Production Stripe",
)
intg = await kp.integrations.update("uuid-…", name="Stripe Live")
await kp.integrations.delete("uuid-…")

# OAuth-linked accounts (the user's authorized Stripe/HubSpot/etc. accounts)
accounts = await kp.integrations.list_accounts(app_slug="stripe")
# get_connect_token() takes no args — token is project-scoped, not app-scoped
token = await kp.integrations.get_connect_token()
# Redirect the user to a Pipedream Connect URL built with token.token

# Action introspection — the action_id is positional
schema = await kp.integrations.get_action_schema("stripe-create-customer")
await kp.integrations.configure_action_prop(
    "stripe-create-customer",
    prop_name="customer",
    configured_props={"email": "{{event.from}}"},
)
await kp.integrations.reload_action_props("stripe-create-customer")
```

> See [`docs/cookbook-integrations.md`](./cookbook-integrations.md) for in-depth patterns: OAuth connect-token flow, app/action discovery, action prop configuration.

> Note: there is no `kp.integrations.get(integration_id)` method to fetch a single saved integration by ID. To find one by ID, fetch the list and filter — or [open an issue](https://github.com/MRCORD/whatsapp-cloud-api-python/issues) if you need it.

### WhatsApp Flows

Manage WhatsApp Flow definitions, versions, and the data endpoint lifecycle.

```python
# Flows (top-level)
flows = await kp.whatsapp_flows.list(status="published")
async for f in kp.whatsapp_flows.iter():
    ...
flow = await kp.whatsapp_flows.get("uuid-…")
flow = await kp.whatsapp_flows.create(
    name="Onboarding",
    phone_number_id="uuid-…",
    flow_json={"version": "3.0", "screens": [...]},
)
await kp.whatsapp_flows.publish("uuid-flow")
result = await kp.whatsapp_flows.setup_encryption("uuid-flow", phone_number_id="uuid-…")

# Versions
versions = await kp.whatsapp_flows.list_versions("uuid-flow")
v = await kp.whatsapp_flows.get_version("uuid-flow", "uuid-version")
v = await kp.whatsapp_flows.create_version(
    "uuid-flow",
    flow_json={"version": "3.0", "screens": [...]},
)

# Data endpoint lifecycle (the serverless function backing the flow)
endpoint = await kp.whatsapp_flows.get_data_endpoint("uuid-flow")
endpoint = await kp.whatsapp_flows.upsert_data_endpoint(
    "uuid-flow",
    code="export default { async fetch(req) { ... } }",
)
await kp.whatsapp_flows.deploy_data_endpoint("uuid-flow")
result = await kp.whatsapp_flows.register_data_endpoint_with_meta("uuid-flow")

# Function observability
logs = await kp.whatsapp_flows.get_function_logs("uuid-flow", limit=100)
invocations = await kp.whatsapp_flows.get_function_invocations(
    "uuid-flow",
    status="error",
)
```

## Advanced Usage

### Custom retry behavior

```python
# Disable retries (e.g. for tests)
kp = KapsoPlatformClient(api_key="…", max_retries=0)

# Aggressive retry with longer base
kp = KapsoPlatformClient(api_key="…", max_retries=10, retry_backoff=2.0)
```

### Reading rate-limit state

`request()` and `request_raw()` don't expose response headers directly, but `RateLimitError.retry_after` carries the `Retry-After` value when a 429 occurs. For deeper instrumentation, drop down to `httpx` directly via `client._http.get_client()`.

### Pointing at a staging environment

```python
kp = KapsoPlatformClient(
    api_key="…",
    base_url="https://api.staging.kapso.ai/platform/v1",
)
```

### Mixing both clients

A single application typically uses both clients side-by-side: `KapsoPlatformClient` for project management, `WhatsAppClient` for sending/receiving messages. They share auth (the same project API key) and the same exception types, but have separate connection pools.

```python
from kapso_whatsapp import WhatsAppClient, KapsoPlatformClient

api_key = os.environ["KAPSO_API_KEY"]

async with KapsoPlatformClient(api_key=api_key) as kp, \
           WhatsAppClient(kapso_api_key=api_key) as wa:
    customer = await kp.customers.create(name="Acme")
    link = await kp.setup_links.create(customer_id=customer.id)
    # … later, after they connect:
    await wa.messages.send_text(
        phone_number_id="…",
        to="+15551234567",
        body=f"Welcome {customer.name}!",
    )
```
