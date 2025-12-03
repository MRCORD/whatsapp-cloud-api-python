#!/usr/bin/env python3
"""Example: Media upload, download, and messaging."""

import asyncio
import os
from pathlib import Path

from kapso_whatsapp import WhatsAppClient


async def main() -> None:
    """Demonstrate media operations."""
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
        # Upload a local image
        print("Uploading image...")
        image_path = Path("sample_image.jpg")

        if image_path.exists():
            with open(image_path, "rb") as f:
                upload_response = await client.media.upload(
                    phone_number_id=phone_number_id,
                    file=f.read(),
                    mime_type="image/jpeg",
                    filename="sample_image.jpg",
                )
            media_id = upload_response.id
            print(f"  Uploaded: {media_id}")

            # Send the uploaded image
            print("Sending uploaded image...")
            response = await client.messages.send_image(
                phone_number_id=phone_number_id,
                to=recipient,
                image={"id": media_id},
                caption="Image uploaded via SDK",
            )
            print(f"  Sent: {response.message_id}")

            # Get media URL
            print("Getting media URL...")
            url_response = await client.media.get_url(media_id=media_id)
            print(f"  URL: {url_response.url}")

            # Download media
            print("Downloading media...")
            media_bytes = await client.media.download(media_id=media_id)
            print(f"  Downloaded: {len(media_bytes)} bytes")

            # Delete media
            print("Deleting media...")
            await client.media.delete(media_id=media_id)
            print("  Deleted successfully")
        else:
            print(f"  Skipping upload: {image_path} not found")

        # Send image from URL (no upload needed)
        print("\nSending image from URL...")
        response = await client.messages.send_image(
            phone_number_id=phone_number_id,
            to=recipient,
            image={"link": "https://picsum.photos/800/600"},
            caption="Image from URL",
        )
        print(f"  Sent: {response.message_id}")

        # Send document
        print("Sending document from URL...")
        response = await client.messages.send_document(
            phone_number_id=phone_number_id,
            to=recipient,
            document={"link": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"},
            filename="sample.pdf",
            caption="Sample PDF document",
        )
        print(f"  Sent: {response.message_id}")

        # Send video
        print("Sending video from URL...")
        response = await client.messages.send_video(
            phone_number_id=phone_number_id,
            to=recipient,
            video={"link": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"},
            caption="Sample video",
        )
        print(f"  Sent: {response.message_id}")

        print("\nAll media operations completed!")


if __name__ == "__main__":
    asyncio.run(main())
