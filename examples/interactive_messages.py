#!/usr/bin/env python3
"""Example: Sending interactive messages (buttons and lists)."""

import asyncio
import os

from kapso_whatsapp import WhatsAppClient


async def main() -> None:
    """Demonstrate interactive message types."""
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
        # Send interactive buttons
        print("Sending button message...")
        response = await client.messages.send_interactive_buttons(
            phone_number_id=phone_number_id,
            to=recipient,
            body_text="How would you rate our service?",
            buttons=[
                {"id": "rating_great", "title": "Great!"},
                {"id": "rating_ok", "title": "It's OK"},
                {"id": "rating_bad", "title": "Not good"},
            ],
            header={"type": "text", "text": "Quick Survey"},
            footer_text="Tap a button to respond",
        )
        print(f"  Sent: {response.message_id}")

        # Send interactive list
        print("Sending list message...")
        response = await client.messages.send_interactive_list(
            phone_number_id=phone_number_id,
            to=recipient,
            body_text="Select an appointment time:",
            button_text="View Times",
            sections=[
                {
                    "title": "Morning",
                    "rows": [
                        {"id": "time_9am", "title": "9:00 AM", "description": "Early slot"},
                        {"id": "time_10am", "title": "10:00 AM", "description": "Mid-morning"},
                        {"id": "time_11am", "title": "11:00 AM", "description": "Late morning"},
                    ],
                },
                {
                    "title": "Afternoon",
                    "rows": [
                        {"id": "time_2pm", "title": "2:00 PM", "description": "After lunch"},
                        {"id": "time_3pm", "title": "3:00 PM", "description": "Mid-afternoon"},
                        {"id": "time_4pm", "title": "4:00 PM", "description": "Late afternoon"},
                    ],
                },
            ],
            header={"type": "text", "text": "Appointment Booking"},
            footer_text="Select your preferred time",
        )
        print(f"  Sent: {response.message_id}")

        # Send CTA URL button
        print("Sending CTA URL button...")
        response = await client.messages.send_interactive_cta_url(
            phone_number_id=phone_number_id,
            to=recipient,
            body_text="Complete your purchase on our website",
            display_text="Shop Now",
            url="https://example.com/shop",
            header={"type": "text", "text": "Complete Your Order"},
            footer_text="Free shipping on orders over $50",
        )
        print(f"  Sent: {response.message_id}")

        print("\nAll interactive messages sent!")


if __name__ == "__main__":
    asyncio.run(main())
