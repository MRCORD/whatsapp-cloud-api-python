# Cookbook: Integrations

Kapso integrations connect your project to third-party apps — Stripe, HubSpot, Slack, and hundreds
more — through a Pipedream-backed infrastructure. Each app exposes one or more **actions** (discrete
operations like "create a customer" or "send a message"). Before an action can run, the end-user
must authorize the app via OAuth, producing a **connected account**. You configure how an action
maps to your data using **props**. Once fully configured, you save the whole thing as an
**integration record** that your automation workflows reference at runtime.

This cookbook walks the full lifecycle: discovering apps and actions, guiding a user through OAuth,
binding props to event data, keeping schemas fresh, and managing integration records.

---

## Table of Contents

- [OAuth connect-token flow](#oauth-connect-token-flow)
- [Listing apps and actions](#listing-apps-and-actions)
- [Configuring an action](#configuring-an-action)
- [Reload pattern](#reload-pattern)
- [CRUD on integration records](#crud-on-integration-records)

---

## OAuth connect-token flow

The connect-token flow is how an end-user authorizes a third-party app. Your backend generates a
short-lived token; you redirect the user to the Pipedream Connect URL that token unlocks; after
they complete OAuth, the new connected account appears in `list_accounts()`.

### Step 1 — generate a token and redirect the user

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def start_stripe_oauth(request):
    """
    Called from your HTTP handler when a user clicks "Connect Stripe".
    Returns the redirect URL to send them to.
    """
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        token = await kp.integrations.get_connect_token()
        # token.token  — the short-lived bearer value
        # token.expires_at — ISO-8601 timestamp after which the token is invalid

        # Build the Pipedream Connect URL. The base URL is provided by Kapso/Pipedream;
        # replace with the URL from your Kapso dashboard if it differs.
        connect_url = (
            f"https://pipedream.com/_/auth/connect"
            f"?token={token.token}"
            f"&app=stripe"
        )
        return connect_url
```

The user lands on Pipedream's hosted OAuth page, authorizes Stripe, and is redirected back to
whichever success URL you configured in your Kapso project settings.

### Step 2 — confirm the account appeared

After the redirect completes, call `list_accounts()` to verify the new account is visible and
healthy before proceeding.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def verify_stripe_connected():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        accounts = await kp.integrations.list_accounts(app_slug="stripe")

        healthy = [a for a in accounts if a.healthy]
        if not healthy:
            print("No healthy Stripe accounts found yet — the OAuth may still be in flight.")
            return None

        account = healthy[0]
        print(f"Connected: {account.account_name} (id={account.id})")
        print(f"Pipedream account id: {account.pipedream_account_id}")
        return account
```

`ConnectedAccount` fields relevant here:

| Field | Type | Meaning |
|---|---|---|
| `id` | `str` | Kapso-side account UUID |
| `pipedream_account_id` | `str` | Pipedream's identifier — pass this when configuring props |
| `app_slug` | `str` | App identifier (e.g. `"stripe"`) |
| `account_name` | `str \| None` | Display name the user gave the account |
| `healthy` | `bool` | `False` means the OAuth token has expired or been revoked |

### Step 3 — handle token expiry

`get_connect_token()` returns a token that expires (see `expires_at`). If the user takes too long,
generate a fresh one and restart the redirect. There is no server-side refresh; each connect
session needs its own token.

```python
from datetime import datetime, timezone

async def get_fresh_connect_url(kp: KapsoPlatformClient, app: str) -> str:
    token = await kp.integrations.get_connect_token()
    expires = datetime.fromisoformat(token.expires_at)
    if expires <= datetime.now(timezone.utc):
        # This shouldn't happen on a freshly minted token, but guard defensively.
        raise RuntimeError("Token expired immediately — check your system clock.")
    return f"https://pipedream.com/_/auth/connect?token={token.token}&app={app}"
```

---

## Listing apps and actions

### Discover available apps

`list_apps()` queries Pipedream's catalog. Use it to populate a "Choose an app" picker in your UI.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def show_app_catalog():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        # All apps with actions (the most common filter for integration builders)
        apps = await kp.integrations.list_apps(has_actions=True, limit=100)

        for app in apps:
            print(f"{app.name_slug:30s}  {app.name}")
```

`list_apps()` parameters:

| Parameter | Default | Effect |
|---|---|---|
| `query` | `None` | Text search across app names |
| `has_components` | `None` | Only apps that have any Pipedream component |
| `has_actions` | `None` | Only apps that have action components |
| `has_triggers` | `None` | Only apps that have trigger components |
| `limit` | `50` | Max results |

Search example — finding CRM apps:

```python
async def search_crm_apps():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        apps = await kp.integrations.list_apps(query="crm", has_actions=True)
        # Returns HubSpot, Salesforce, Pipedrive, etc.
        for app in apps:
            print(app.name_slug, "—", app.description)
```

### Discover actions for an app

Once you know which app a user wants to work with, fetch its actions with `list_actions()`.

```python
async def list_hubspot_actions():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        actions = await kp.integrations.list_actions(app_slug="hubspot")

        for action in actions:
            print(f"  key={action.key}")
            print(f"  name={action.name}")
            print(f"  version={action.version}")
            print()
```

`list_actions()` parameters:

| Parameter | Default | Effect |
|---|---|---|
| `app_slug` | `None` | Filter to a specific app (e.g. `"slack"`, `"hubspot"`) |
| `query` | `None` | Free-text search across action names and descriptions |

### Building a two-level picker

Here is a minimal pattern for a "select app then select action" UI flow:

```python
async def build_action_picker(app_slug: str) -> list[dict]:
    """
    Returns a list of {key, name, description} dicts ready for a <select> element.
    """
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        actions = await kp.integrations.list_actions(app_slug=app_slug)
        return [
            {
                "value": action.key,
                "label": action.name or action.key,
                "hint": action.description or "",
            }
            for action in actions
            if action.key  # guard against catalog entries missing a key
        ]

# Example usage:
# slack_actions = asyncio.run(build_action_picker("slack"))
# => [{"value": "slack-send-message", "label": "Send Message", ...}, ...]
```

---

## Configuring an action

Before saving an integration you need to understand what props the action requires, then bind
values to each prop. Pipedream props come in two flavors:

- **Static props** — a fixed value (a string, number, or boolean) set once at configuration time.
- **Dynamic props** — options that depend on the connected account or previously set props (e.g.
  "which Slack channel?"). These are fetched at configuration time via `configure_action_prop()`.

### Step 1 — inspect the action schema

```python
async def inspect_slack_send_message():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        schema = await kp.integrations.get_action_schema("slack-send-message")

        # The schema is a raw dict whose structure mirrors the Pipedream component definition.
        # Common top-level keys: "props", "name", "version", "key".
        props = schema.get("props", {})
        for prop_name, prop_def in props.items():
            print(f"{prop_name}: type={prop_def.get('type')} label={prop_def.get('label')}")
```

A typical schema for `slack-send-message` looks like:

```json
{
  "key": "slack-send-message",
  "name": "Send Message",
  "version": "0.3.2",
  "props": {
    "slack": {
      "type": "app",
      "app": "slack"
    },
    "channel": {
      "type": "string",
      "label": "Channel",
      "description": "The Slack channel to send to",
      "options": "dynamic"
    },
    "text": {
      "type": "string",
      "label": "Message Text"
    },
    "as_user": {
      "type": "boolean",
      "label": "Send as User",
      "optional": true
    }
  }
}
```

The `"app"` prop (`slack` above) is how the action references the connected account. You will
provide the `pipedream_account_id` of the connected Slack account for this prop.

### Step 2 — fetch dynamic options for a prop

For props whose options depend on runtime context (channel lists, board IDs, pipeline stages, etc.),
call `configure_action_prop()`. Pass the current values of any already-configured props so the API
can resolve options that depend on them.

```python
async def get_slack_channels(pipedream_account_id: str) -> list[dict]:
    """
    Returns the list of Slack channels the connected account can post to.

    Args:
        pipedream_account_id: The ConnectedAccount.pipedream_account_id value.
    """
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        options = await kp.integrations.configure_action_prop(
            "slack-send-message",
            prop_name="channel",
            configured_props={
                # The "app" prop must reference the Pipedream account auth provision.
                "slack": {"authProvisionId": pipedream_account_id},
            },
        )
        # options is a list of {"label": "...", "value": "..."} dicts.
        return options

# Example output:
# [
#   {"label": "#general", "value": "C01234ABCDE"},
#   {"label": "#sales", "value": "C09876ZYXWV"},
# ]
```

### Step 3 — bind props to event data

Once you know the available options, you bind prop values. Static values go in directly. For
template-style bindings (mapping a prop to a field from the triggering WhatsApp event), use
Kapso's `{{event.field}}` syntax.

```python
async def configure_slack_notification(
    pipedream_account_id: str,
    channel_id: str,
) -> dict:
    """
    Build the configured_props dict for a "new WhatsApp message → Slack notification" integration.
    """
    return {
        "slack": {"authProvisionId": pipedream_account_id},
        "channel": channel_id,              # static: always post to this channel
        "text": "New WhatsApp message from {{event.from}}: {{event.body}}",
    }
```

`configure_action_prop()` parameters:

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action_id` | `str` | yes | Pipedream action key (first positional arg) |
| `prop_name` | `str` | yes | Which prop you want options for |
| `configured_props` | `dict \| None` | no | Current prop values; needed for context-dependent options |
| `dynamic_props_id` | `str \| None` | no | Session ID if you are mid-configuration (see below) |

### Full HubSpot example — create a contact

This shows the complete configuration loop for `hubspot-create-contact`:

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def configure_hubspot_create_contact(pipedream_account_id: str):
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:

        # 1. Inspect what the action needs
        schema = await kp.integrations.get_action_schema("hubspot-create-contact")
        print("Action:", schema.get("name"))

        # 2. Fetch pipeline options (context-dependent prop)
        pipeline_options = await kp.integrations.configure_action_prop(
            "hubspot-create-contact",
            prop_name="pipeline",
            configured_props={
                "hubspot": {"authProvisionId": pipedream_account_id},
            },
        )
        # e.g. [{"label": "Sales Pipeline", "value": "default"}, ...]
        pipeline_id = pipeline_options[0]["value"] if pipeline_options else "default"

        # 3. Build the final configured_props, binding some fields to event data
        configured_props = {
            "hubspot": {"authProvisionId": pipedream_account_id},
            "pipeline": pipeline_id,
            "email": "{{event.from_email}}",
            "firstname": "{{event.contact_name}}",
            "phone": "{{event.from}}",
        }

        # 4. Save as an integration record
        integration = await kp.integrations.create(
            action_id="hubspot-create-contact",
            app_slug="hubspot",
            app_name="HubSpot",
            name="WhatsApp Lead → HubSpot Contact",
            configured_props=configured_props,
        )
        print(f"Created integration: {integration.id}")
        return integration

asyncio.run(configure_hubspot_create_contact("pd_acc_…"))
```

---

## Reload pattern

Third-party app schemas evolve. Pipedream occasionally updates prop definitions — new optional
fields appear, select options expand, defaults change. When your UI detects that a stored
`dynamic_props_id` is stale, or after a connected account's token refreshes, call
`reload_action_props()` to get a fresh set of prop definitions.

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def refresh_stripe_action_props(
    dynamic_props_id: str,
    pipedream_account_id: str,
):
    """
    Reload props for stripe-create-customer after a schema change or token refresh.

    Args:
        dynamic_props_id:       The session ID from a previous configure_action_prop call.
        pipedream_account_id:   The ConnectedAccount.pipedream_account_id.
    """
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        refreshed_props = await kp.integrations.reload_action_props(
            "stripe-create-customer",
            configured_props={
                "stripe": {"authProvisionId": pipedream_account_id},
            },
            dynamic_props_id=dynamic_props_id,
        )

        # refreshed_props is a list of updated prop definition dicts.
        for prop in refreshed_props:
            print(f"prop: {prop.get('name')} — {prop.get('type')}")

        return refreshed_props
```

`reload_action_props()` parameters:

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action_id` | `str` | yes | Pipedream action key (first positional arg) |
| `configured_props` | `dict \| None` | no | Current prop values for context |
| `dynamic_props_id` | `str \| None` | no | Existing session ID to reload |

When to call `reload_action_props()`:

- After a user reconnects their OAuth account (their `pipedream_account_id` may change).
- When your UI shows a configuration form and the cached prop list is more than a few hours old.
- When `configure_action_prop()` returns options that no longer match what the user sees in the
  third-party app (e.g. a Slack channel was added/removed).

---

## CRUD on integration records

An integration record is a saved, named configuration of an action. Workflow automations reference
these records by ID at runtime.

### Create

```python
import asyncio
from kapso_whatsapp import KapsoPlatformClient

async def create_stripe_integration(pipedream_account_id: str):
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        integration = await kp.integrations.create(
            action_id="stripe-create-customer",
            app_slug="stripe",
            app_name="Stripe",
            name="Create Stripe Customer on First Message",
            configured_props={
                "stripe": {"authProvisionId": pipedream_account_id},
                "email": "{{event.contact.email}}",
                "name": "{{event.contact.name}}",
            },
        )
        print(f"Created: {integration.id}")
        return integration
```

`create()` parameters:

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action_id` | `str` | yes | Pipedream action key |
| `app_slug` | `str` | yes | App identifier (e.g. `"stripe"`) |
| `app_name` | `str \| None` | no | Human-readable app name |
| `name` | `str \| None` | no | Display name for this integration record |
| `configured_props` | `dict \| None` | no | Prop values (auth provision IDs + data bindings) |
| `variable_definitions` | `dict \| None` | no | Variable schema for parameterized integrations |
| `dynamic_props_id` | `str \| None` | no | Dynamic props session ID |

### List

```python
async def list_all_integrations():
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        integrations = await kp.integrations.list()
        for intg in integrations:
            status = "enabled" if intg.enabled else "disabled"
            print(f"[{status}] {intg.name or intg.id} — {intg.app_name} / {intg.action_name}")
```

`list()` takes no parameters and returns all saved integrations for the project. It is not
paginated — the response fits in a single list.

### Update

```python
async def rename_integration(integration_id: str):
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        updated = await kp.integrations.update(
            integration_id,
            name="Stripe Customer Creation (Production)",
        )
        print(f"Renamed: {updated.name}")

async def rebind_props(integration_id: str, new_pipedream_account_id: str):
    """Use this after a user reconnects their OAuth account."""
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        updated = await kp.integrations.update(
            integration_id,
            configured_props={
                "stripe": {"authProvisionId": new_pipedream_account_id},
                "email": "{{event.contact.email}}",
                "name": "{{event.contact.name}}",
            },
        )
        print(f"Props rebound on: {updated.id}")
```

`update()` is a partial update (PATCH): only the fields you pass are changed.

`update()` parameters:

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `integration_id` | `str` | yes | UUID of the integration record (first positional arg) |
| `name` | `str \| None` | no | New display name |
| `configured_props` | `dict \| None` | no | Replacement prop values |
| `variable_definitions` | `dict \| None` | no | Updated variable schema |
| `dynamic_props_id` | `str \| None` | no | Updated dynamic props session ID |

### Delete

```python
async def remove_integration(integration_id: str):
    async with KapsoPlatformClient(api_key="kp_live_…") as kp:
        result = await kp.integrations.delete(integration_id)
        # result is {"success": True} on success
        print("Deleted:", result)
```

`delete()` returns the raw `{"success": true}` dict from the API. It does not raise on a
successful deletion — check `result["success"]` if you need to assert it programmatically.

---

## Quick reference

| Task | Method |
|---|---|
| Generate OAuth connect URL | `get_connect_token()` |
| List connected OAuth accounts | `list_accounts(app_slug=…)` |
| Browse the app catalog | `list_apps(has_actions=True, query=…)` |
| Browse actions for an app | `list_actions(app_slug=…)` |
| Inspect prop schema for an action | `get_action_schema(action_id)` |
| Fetch options for a dynamic prop | `configure_action_prop(action_id, prop_name=…, configured_props=…)` |
| Refresh stale prop definitions | `reload_action_props(action_id, configured_props=…, dynamic_props_id=…)` |
| Save a configured action | `create(action_id=…, app_slug=…, configured_props=…)` |
| List saved integrations | `list()` |
| Update a saved integration | `update(integration_id, …)` |
| Delete a saved integration | `delete(integration_id)` |
