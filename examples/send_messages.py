#!/usr/bin/env python3
"""Example: Sending different types of messages."""

import asyncio
import os

from kapso_whatsapp import WhatsAppClient


async def main() -> None:
    """Demonstrate sending various message types."""
    # Get credentials from environment
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
        # Send a text message
        print("Sending text message...")
        response = await client.messages.send_text(
            phone_number_id=phone_number_id,
            to=recipient,
            body="Hello from the Python SDK!",
        )
        print(f"  Sent: {response.message_id}")

        # Send a text with URL preview
        print("Sending message with URL preview...")
        response = await client.messages.send_text(
            phone_number_id=phone_number_id,
            to=recipient,
            body="Check out https://kapso.ai",
            preview_url=True,
        )
        print(f"  Sent: {response.message_id}")

        # Send an image from URL
        print("Sending image...")
        response = await client.messages.send_image(
            phone_number_id=phone_number_id,
            to=recipient,
            image={"link": "https://picsum.photos/400/300"},
            caption="A random image",
        )
        print(f"  Sent: {response.message_id}")

        # Send a location
        print("Sending location...")
        response = await client.messages.send_location(
            phone_number_id=phone_number_id,
            to=recipient,
            latitude=37.7749,
            longitude=-122.4194,
            name="San Francisco",
            address="California, USA",
        )
        print(f"  Sent: {response.message_id}")

        print("\nAll messages sent successfully!")


if __name__ == "__main__":
    asyncio.run(main())
