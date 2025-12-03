"""
Messages Resource

Handles all message sending operations including text, interactive,
media, location, contact, template, and reaction messages.

Ported from flowers-backend with TypeScript SDK alignment.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..types import (
    Contact,
    ListMessagesResponse,
    LocationInput,
    MediaInput,
    MessageDirection,
    MessageStatus,
    ReplyContext,
    SendMessageResponse,
    TemplateSendPayload,
    TextMessageInput,
)
from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class MessagesResource(BaseResource):
    """
    WhatsApp messages operations.

    Provides methods for sending all types of WhatsApp messages:
    - Text messages
    - Media messages (image, video, audio, document, sticker)
    - Interactive messages (buttons, lists, CTA URL, flows)
    - Template messages
    - Location messages
    - Contact cards
    - Reactions

    Example:
        >>> async with WhatsAppClient(access_token="...") as client:
        ...     response = await client.messages.send_text(
        ...         phone_number_id="123456",
        ...         to="+15551234567",
        ...         body="Hello!"
        ...     )
        ...     print(f"Sent: {response.message_id}")
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    # =========================================================================
    # Text Messages
    # =========================================================================

    async def send_text(
        self,
        *,
        phone_number_id: str,
        to: str,
        body: str,
        preview_url: bool = False,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a text message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number (E.164 format)
            body: Message text (max 4096 characters)
            preview_url: Enable URL preview in message
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_text(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body="Hello! Your order has been shipped."
            ... )
            >>> # Reply to a message
            >>> await client.messages.send_text(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body="This is a reply",
            ...     context={"message_id": "wamid.xxx"}
            ... )
        """
        message = TextMessageInput(
            phone_number_id=phone_number_id,
            to=to,
            body=body,
            preview_url=preview_url,
        )

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.to,
            "type": "text",
            "text": {
                "body": message.body,
                "preview_url": message.preview_url,
            },
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending text message to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Media Messages
    # =========================================================================

    async def send_image(
        self,
        *,
        phone_number_id: str,
        to: str,
        image: MediaInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send an image message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            image: Image media (with id or link, optional caption)
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_image(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     image={"link": "https://example.com/photo.jpg", "caption": "Check this!"}
            ... )
        """
        if isinstance(image, dict):
            image = MediaInput.model_validate(image)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": image.model_dump(exclude_none=True, by_alias=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending image to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_video(
        self,
        *,
        phone_number_id: str,
        to: str,
        video: MediaInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """Send a video message."""
        if isinstance(video, dict):
            video = MediaInput.model_validate(video)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "video",
            "video": video.model_dump(exclude_none=True, by_alias=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending video to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_audio(
        self,
        *,
        phone_number_id: str,
        to: str,
        audio: MediaInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send an audio message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            audio: Audio media (with id or link). Set voice=True for voice notes.
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> # Send audio file
            >>> await client.messages.send_audio(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     audio={"id": "media-id-here"}
            ... )
            >>> # Send voice note (plays inline)
            >>> await client.messages.send_audio(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     audio={"id": "media-id-here", "voice": True}
            ... )
        """
        if isinstance(audio, dict):
            audio = MediaInput.model_validate(audio)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": audio.model_dump(exclude_none=True, by_alias=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending audio to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_document(
        self,
        *,
        phone_number_id: str,
        to: str,
        document: MediaInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """Send a document message."""
        if isinstance(document, dict):
            document = MediaInput.model_validate(document)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": document.model_dump(exclude_none=True, by_alias=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending document to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_sticker(
        self,
        *,
        phone_number_id: str,
        to: str,
        sticker: MediaInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """Send a sticker message."""
        if isinstance(sticker, dict):
            sticker = MediaInput.model_validate(sticker)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "sticker",
            "sticker": sticker.model_dump(exclude_none=True, by_alias=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending sticker to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Location Messages
    # =========================================================================

    async def send_location(
        self,
        *,
        phone_number_id: str,
        to: str,
        location: LocationInput | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a location message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            location: Location with latitude, longitude, optional name and address
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_location(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     location={"latitude": -33.45, "longitude": -70.66, "name": "Santiago"}
            ... )
        """
        if isinstance(location, dict):
            location = LocationInput.model_validate(location)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "location",
            "location": location.model_dump(exclude_none=True),
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending location to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Contact Messages
    # =========================================================================

    async def send_contacts(
        self,
        *,
        phone_number_id: str,
        to: str,
        contacts: list[Contact | dict[str, Any]],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send contact card(s).

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            contacts: List of contact cards
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_contacts(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     contacts=[{
            ...         "name": {"formattedName": "John Doe"},
            ...         "phones": [{"phone": "+15559876543", "type": "CELL"}]
            ...     }]
            ... )
        """
        validated_contacts = [
            c if isinstance(c, Contact) else Contact.model_validate(c)
            for c in contacts
        ]

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "contacts",
            "contacts": [c.model_dump(exclude_none=True, by_alias=True) for c in validated_contacts],
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending {len(contacts)} contact(s) to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Reaction Messages
    # =========================================================================

    async def send_reaction(
        self,
        *,
        phone_number_id: str,
        to: str,
        reaction: dict[str, str],
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a reaction to a message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            reaction: Dict with message_id and emoji (empty emoji removes reaction)
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_reaction(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     reaction={"message_id": "wamid...", "emoji": "👍"}
            ... )
        """
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "reaction",
            "reaction": {
                "message_id": reaction.get("message_id") or reaction.get("messageId"),
                "emoji": reaction.get("emoji", ""),
            },
        }

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending reaction to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Interactive Messages
    # =========================================================================

    async def send_interactive_buttons(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header: dict[str, Any] | None = None,
        header_text: str | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send an interactive button message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Main message text
            buttons: List of buttons (max 3), each with id and title
            header: Optional header (type: text/image/video/document)
            header_text: Simple text header (alternative to header dict)
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_buttons(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Would you like to proceed?",
            ...     buttons=[
            ...         {"id": "yes", "title": "Yes"},
            ...         {"id": "no", "title": "No"}
            ...     ]
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"][:20]}}
                    for btn in buttons[:3]
                ]
            },
        }

        if header:
            interactive["header"] = header
        elif header_text:
            interactive["header"] = {"type": "text", "text": header_text}

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending interactive buttons to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_list(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        button_text: str,
        sections: list[dict[str, Any]],
        header_text: str | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send an interactive list message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Main message text
            button_text: CTA button text
            sections: List of sections with title and rows
            header_text: Optional header text
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_list(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Choose an option:",
            ...     button_text="View Options",
            ...     sections=[{
            ...         "title": "Options",
            ...         "rows": [
            ...             {"id": "1", "title": "Option 1", "description": "First option"},
            ...             {"id": "2", "title": "Option 2", "description": "Second option"}
            ...         ]
            ...     }]
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": [
                    {
                        "title": section.get("title", "Options")[:24],
                        "rows": [
                            {
                                "id": row["id"],
                                "title": row["title"][:24],
                                **({"description": row["description"][:72]} if row.get("description") else {}),
                            }
                            for row in section.get("rows", [])
                        ],
                    }
                    for section in sections
                ],
            },
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending interactive list to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_cta_url(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        parameters: dict[str, str],
        header: dict[str, Any] | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a CTA URL button message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Main message text
            parameters: Dict with display_text and url
            header: Optional header
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_cta_url(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Check out our website!",
            ...     parameters={"display_text": "Visit Site", "url": "https://example.com"}
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "cta_url",
            "body": {"text": body_text},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": parameters.get("display_text") or parameters.get("displayText"),
                    "url": parameters["url"],
                },
            },
        }

        if header:
            interactive["header"] = header

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending CTA URL to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_flow(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        parameters: dict[str, Any],
        header: dict[str, Any] | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a Flow message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Main message text
            parameters: Flow parameters (flow_id, flow_cta, flow_token, etc.)
            header: Optional header
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_flow(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Complete this form",
            ...     parameters={
            ...         "flow_id": "12345",
            ...         "flow_cta": "Start",
            ...         "flow_token": "token123"
            ...     }
            ... )
        """
        flow_params = {
            "flow_id": parameters.get("flow_id") or parameters.get("flowId"),
            "flow_cta": parameters.get("flow_cta") or parameters.get("flowCta"),
            "flow_message_version": parameters.get("flow_message_version") or parameters.get("flowMessageVersion", "3"),
        }

        if flow_token := (parameters.get("flow_token") or parameters.get("flowToken")):
            flow_params["flow_token"] = flow_token

        if flow_action := (parameters.get("flow_action") or parameters.get("flowAction")):
            flow_params["flow_action"] = flow_action

        if flow_action_payload := (parameters.get("flow_action_payload") or parameters.get("flowActionPayload")):
            flow_params["flow_action_payload"] = flow_action_payload

        interactive: dict[str, Any] = {
            "type": "flow",
            "body": {"text": body_text},
            "action": {
                "name": "flow",
                "parameters": flow_params,
            },
        }

        if header:
            interactive["header"] = header

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending flow message to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_location_request(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a location request message.

        Requests the user to share their location.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Message text explaining why you need their location
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_location_request(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Please share your location for delivery"
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "location_request_message",
            "body": {"text": body_text},
            "action": {"name": "send_location"},
        }

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending location request to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_product(
        self,
        *,
        phone_number_id: str,
        to: str,
        catalog_id: str,
        product_retailer_id: str,
        body_text: str | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a single product message.

        Shows a single product from your catalog.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            catalog_id: Facebook catalog ID
            product_retailer_id: Product retailer ID from your catalog
            body_text: Optional message body text
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_product(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     catalog_id="catalog123",
            ...     product_retailer_id="SKU001",
            ...     body_text="Check out this product!"
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "product",
            "action": {
                "catalog_id": catalog_id,
                "product_retailer_id": product_retailer_id,
            },
        }

        if body_text:
            interactive["body"] = {"text": body_text}

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending product message to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_product_list(
        self,
        *,
        phone_number_id: str,
        to: str,
        catalog_id: str,
        sections: list[dict[str, Any]],
        header_text: str,
        body_text: str,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a multi-product message.

        Shows multiple products from your catalog organized in sections.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            catalog_id: Facebook catalog ID
            sections: List of sections, each with title and product_items
            header_text: Header text (required)
            body_text: Message body text (required)
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_product_list(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     catalog_id="catalog123",
            ...     header_text="Our Products",
            ...     body_text="Choose from our selection",
            ...     sections=[{
            ...         "title": "Popular Items",
            ...         "product_items": [
            ...             {"product_retailer_id": "SKU001"},
            ...             {"product_retailer_id": "SKU002"}
            ...         ]
            ...     }]
            ... )
        """
        interactive: dict[str, Any] = {
            "type": "product_list",
            "header": {"type": "text", "text": header_text},
            "body": {"text": body_text},
            "action": {
                "catalog_id": catalog_id,
                "sections": sections,
            },
        }

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending product list to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    async def send_interactive_catalog(
        self,
        *,
        phone_number_id: str,
        to: str,
        body_text: str,
        thumbnail_product_retailer_id: str | None = None,
        footer_text: str | None = None,
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a catalog message.

        Allows users to browse your entire product catalog.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            body_text: Message body text
            thumbnail_product_retailer_id: Product ID to use as thumbnail (optional)
            footer_text: Optional footer text
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_interactive_catalog(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     body_text="Browse our catalog!",
            ...     thumbnail_product_retailer_id="SKU001"
            ... )
        """
        action: dict[str, Any] = {"name": "catalog_message"}

        if thumbnail_product_retailer_id:
            action["parameters"] = {
                "thumbnail_product_retailer_id": thumbnail_product_retailer_id
            }

        interactive: dict[str, Any] = {
            "type": "catalog_message",
            "body": {"text": body_text},
            "action": action,
        }

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending catalog message to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Template Messages
    # =========================================================================

    async def send_template(
        self,
        *,
        phone_number_id: str,
        to: str,
        template: TemplateSendPayload | dict[str, Any],
        context: ReplyContext | dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        """
        Send a template message.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            to: Recipient phone number
            template: Template payload (name, language, components)
            context: Reply context with message_id to reply to a specific message
            biz_opaque_callback_data: Custom data for webhook tracking (max 512 chars)

        Returns:
            SendMessageResponse with message ID

        Example:
            >>> await client.messages.send_template(
            ...     phone_number_id="123456",
            ...     to="+15551234567",
            ...     template={
            ...         "name": "hello_world",
            ...         "language": "en_US"
            ...     }
            ... )
        """
        if isinstance(template, dict):
            template = TemplateSendPayload.model_validate(template)

        # Build template data
        template_data: dict[str, Any] = {"name": template.name}

        # Handle language (string or object)
        if isinstance(template.language, str):
            template_data["language"] = {"code": template.language}
        else:
            template_data["language"] = template.language.model_dump()

        # Add components if present
        if template.components:
            template_data["components"] = [
                c.model_dump(exclude_none=True, by_alias=True)
                for c in template.components
            ]

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_data,
        }

        if context:
            if isinstance(context, dict):
                payload["context"] = {"message_id": context.get("message_id")}
            else:
                payload["context"] = {"message_id": context.message_id}

        if biz_opaque_callback_data:
            payload["biz_opaque_callback_data"] = biz_opaque_callback_data[:512]

        logger.info(f"Sending template '{template.name}' to {to}")
        response = await self._request("POST", f"{phone_number_id}/messages", json=payload)
        return SendMessageResponse.model_validate(response)

    # =========================================================================
    # Mark as Read
    # =========================================================================

    async def mark_read(
        self,
        *,
        phone_number_id: str,
        message_id: str,
        typing_indicator: bool | None = None,
    ) -> dict[str, Any]:
        """
        Mark a message as read.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            message_id: ID of message to mark as read
            typing_indicator: If true, shows typing indicator while processing

        Returns:
            API response

        Example:
            >>> await client.messages.mark_read(
            ...     phone_number_id="123456",
            ...     message_id="wamid..."
            ... )
            >>> # With typing indicator
            >>> await client.messages.mark_read(
            ...     phone_number_id="123456",
            ...     message_id="wamid...",
            ...     typing_indicator=True
            ... )
        """
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        if typing_indicator is not None:
            payload["typing_indicator"] = typing_indicator

        logger.info(f"Marking message {message_id} as read")
        return await self._request("POST", f"{phone_number_id}/messages", json=payload)

    # =========================================================================
    # Kapso Proxy: Message History
    # =========================================================================

    async def list(
        self,
        *,
        phone_number_id: str,
        conversation_id: str | None = None,
        direction: MessageDirection | str | None = None,
        status: MessageStatus | str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
        fields: str | None = None,
    ) -> ListMessagesResponse:
        """
        List messages for a phone number (Kapso proxy only).

        Retrieve a paginated list of WhatsApp messages with filtering support.
        Uses cursor-based pagination for efficient scrolling through large result sets.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            conversation_id: Filter by conversation ID
            direction: Filter by direction (inbound/outbound)
            status: Filter by message status (pending/sent/delivered/read/failed)
            since: Filter messages created on or after this time (ISO 8601)
            until: Filter messages created on or before this time (ISO 8601)
            limit: Maximum number of results per page (default 20, max 100)
            before: Cursor for previous page (Base64 encoded)
            after: Cursor for next page (Base64 encoded)
            fields: Filter response fields. Use `kapso()` to include Kapso-specific
                   extensions. Example: `fields=kapso(direction,status,processing_status)`

        Returns:
            ListMessagesResponse with messages and pagination info

        Example:
            >>> messages = await client.messages.list(
            ...     phone_number_id="123456",
            ...     direction="inbound",
            ...     status="delivered",
            ...     limit=50
            ... )
            >>> for msg in messages.data:
            ...     print(f"{msg.id}: {msg.type} - {msg.kapso.status}")
        """
        self._require_kapso_proxy()

        params: dict[str, Any] = {"limit": min(limit, 100)}

        if conversation_id:
            params["conversation_id"] = conversation_id
        if direction:
            params["direction"] = direction.value if isinstance(direction, MessageDirection) else direction
        if status:
            params["status"] = status.value if isinstance(status, MessageStatus) else status
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if fields:
            params["fields"] = fields

        response = await self._request("GET", f"{phone_number_id}/messages", params=params)
        return ListMessagesResponse.model_validate(response)

    async def query(
        self,
        *,
        phone_number_id: str,
        conversation_id: str | None = None,
        direction: MessageDirection | str | None = None,
        status: MessageStatus | str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
        fields: str | None = None,
    ) -> ListMessagesResponse:
        """
        Query message history (Kapso proxy only).

        Alias for `list()` method for backward compatibility.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            conversation_id: Filter by conversation ID
            direction: Filter by direction (inbound/outbound)
            status: Filter by message status (pending/sent/delivered/read/failed)
            since: ISO timestamp for start date
            until: ISO timestamp for end date
            limit: Maximum messages to return (default 20, max 100)
            before: Cursor for previous page
            after: Cursor for next page
            fields: Kapso fields to include (e.g., "kapso(media_url)")

        Returns:
            ListMessagesResponse with messages and pagination info

        Example:
            >>> messages = await client.messages.query(
            ...     phone_number_id="123456",
            ...     direction="inbound",
            ...     limit=50
            ... )
        """
        return await self.list(
            phone_number_id=phone_number_id,
            conversation_id=conversation_id,
            direction=direction,
            status=status,
            since=since,
            until=until,
            limit=limit,
            before=before,
            after=after,
            fields=fields,
        )

    async def list_by_conversation(
        self,
        *,
        phone_number_id: str,
        conversation_id: str,
        limit: int = 20,
        before: str | None = None,
        after: str | None = None,
        fields: str | None = None,
    ) -> ListMessagesResponse:
        """
        List messages in a conversation (Kapso proxy only).

        Convenience method that filters by conversation_id.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            conversation_id: Conversation ID to filter messages
            limit: Maximum messages to return (default 20, max 100)
            before: Cursor for previous page
            after: Cursor for next page
            fields: Kapso fields to include

        Returns:
            ListMessagesResponse with messages and pagination info

        Example:
            >>> messages = await client.messages.list_by_conversation(
            ...     phone_number_id="123456",
            ...     conversation_id="conv-uuid-here",
            ...     limit=20
            ... )
        """
        return await self.list(
            phone_number_id=phone_number_id,
            conversation_id=conversation_id,
            limit=limit,
            before=before,
            after=after,
            fields=fields,
        )
