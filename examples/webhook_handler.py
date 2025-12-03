#!/usr/bin/env python3
"""Example: FastAPI webhook handler for WhatsApp messages."""

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request

from kapso_whatsapp import WhatsAppClient
from kapso_whatsapp.webhooks import normalize_webhook, verify_signature

app = FastAPI(title="WhatsApp Webhook Handler")

# Configuration
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "my-verify-token")
APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

# Client instance (reused across requests)
client: WhatsAppClient | None = None


@app.on_event("startup")
async def startup() -> None:
    """Initialize WhatsApp client on startup."""
    global client
    if ACCESS_TOKEN:
        client = WhatsAppClient(access_token=ACCESS_TOKEN)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close client on shutdown."""
    global client
    if client:
        await client.close()


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> int:
    """Handle webhook verification from Meta."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("Webhook verified successfully")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    """Handle incoming webhook events."""
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature if app secret is configured
    if APP_SECRET:
        signature = request.headers.get("x-hub-signature-256", "")
        if not verify_signature(body, signature, APP_SECRET):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse and normalize the payload
    payload = await request.json()
    events = normalize_webhook(payload)

    # Process each event
    for event in events:
        await process_event(event)

    return {"status": "ok"}


async def process_event(event: dict[str, Any]) -> None:
    """Process a single webhook event."""
    event_type = event.get("type")
    direction = event.get("direction")

    print(f"Received event: type={event_type}, direction={direction}")

    # Handle inbound messages
    if direction == "inbound":
        await handle_inbound_message(event)

    # Handle status updates
    elif event_type == "status":
        await handle_status_update(event)


async def handle_inbound_message(event: dict[str, Any]) -> None:
    """Handle incoming messages from users."""
    message_type = event.get("type")
    sender = event.get("from")
    message_id = event.get("id")

    print(f"Message from {sender}: type={message_type}, id={message_id}")

    # Mark as read
    if client and PHONE_NUMBER_ID:
        await client.messages.mark_as_read(
            phone_number_id=PHONE_NUMBER_ID,
            message_id=message_id,
        )

    # Handle different message types
    if message_type == "text":
        text = event.get("text", {}).get("body", "")
        print(f"  Text: {text}")
        await handle_text_message(sender, text)

    elif message_type == "image":
        image = event.get("image", {})
        print(f"  Image: id={image.get('id')}, caption={image.get('caption')}")

    elif message_type == "interactive":
        interactive = event.get("interactive", {})
        interactive_type = interactive.get("type")

        if interactive_type == "button_reply":
            button = interactive.get("button_reply", {})
            print(f"  Button clicked: id={button.get('id')}, title={button.get('title')}")

        elif interactive_type == "list_reply":
            list_item = interactive.get("list_reply", {})
            print(f"  List selected: id={list_item.get('id')}, title={list_item.get('title')}")


async def handle_text_message(sender: str, text: str) -> None:
    """Handle text messages with simple auto-replies."""
    if not client or not PHONE_NUMBER_ID:
        return

    text_lower = text.lower()

    if text_lower in ["hi", "hello", "hey"]:
        await client.messages.send_text(
            phone_number_id=PHONE_NUMBER_ID,
            to=sender,
            body="Hello! How can I help you today?",
        )

    elif text_lower == "help":
        await client.messages.send_interactive_buttons(
            phone_number_id=PHONE_NUMBER_ID,
            to=sender,
            body_text="What would you like help with?",
            buttons=[
                {"id": "help_orders", "title": "My Orders"},
                {"id": "help_support", "title": "Support"},
                {"id": "help_info", "title": "Information"},
            ],
        )


async def handle_status_update(event: dict[str, Any]) -> None:
    """Handle message status updates."""
    status = event.get("status")
    message_id = event.get("id")
    recipient = event.get("recipient_id")

    print(f"Status update: {status} for message {message_id} to {recipient}")

    if status == "failed":
        errors = event.get("errors", [])
        for error in errors:
            print(f"  Error: {error.get('code')} - {error.get('message')}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
