#!/usr/bin/env python3
"""Example: Sending template messages."""

import asyncio
import os

from kapso_whatsapp import WhatsAppClient


async def main() -> None:
    """Demonstrate template message sending."""
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    recipient = os.environ.get("WHATSAPP_TEST_RECIPIENT")

    if not all([access_token, phone_number_id, recipient]):
        print("Please set environment variables:")
        print("  WHATSAPP_ACCESS_TOKEN")
        print("  WHATSAPP_PHONE_NUMBER_ID")
        print("  WHATSAPP_TEST_RECIPIENT")
        return

    async with WhatsAppClient(access_token=access_token) as client:
        # Send simple template (no parameters)
        print("Sending simple template...")
        response = await client.messages.send_template(
            phone_number_id=phone_number_id,
            to=recipient,
            template_name="hello_world",
            language_code="en_US",
        )
        print(f"  Sent: {response.message_id}")

        # Send template with body parameters
        print("Sending template with parameters...")
        response = await client.messages.send_template(
            phone_number_id=phone_number_id,
            to=recipient,
            template_name="order_confirmation",
            language_code="en_US",
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "ORD-12345"},
                        {"type": "text", "text": "$99.99"},
                        {"type": "text", "text": "December 5, 2025"},
                    ],
                }
            ],
        )
        print(f"  Sent: {response.message_id}")

        # Send template with header image
        print("Sending template with header image...")
        response = await client.messages.send_template(
            phone_number_id=phone_number_id,
            to=recipient,
            template_name="promotional_offer",
            language_code="en_US",
            components=[
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {"link": "https://picsum.photos/800/400"},
                        }
                    ],
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "20%"},
                        {"type": "text", "text": "SAVE20"},
                    ],
                },
            ],
        )
        print(f"  Sent: {response.message_id}")

        # Send template with buttons
        print("Sending template with quick reply buttons...")
        response = await client.messages.send_template(
            phone_number_id=phone_number_id,
            to=recipient,
            template_name="appointment_reminder",
            language_code="en_US",
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "Dr. Smith"},
                        {"type": "text", "text": "December 10, 2025 at 2:00 PM"},
                    ],
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [{"type": "payload", "payload": "confirm_apt_123"}],
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [{"type": "payload", "payload": "reschedule_apt_123"}],
                },
            ],
        )
        print(f"  Sent: {response.message_id}")

        print("\nAll template messages sent!")


if __name__ == "__main__":
    asyncio.run(main())
