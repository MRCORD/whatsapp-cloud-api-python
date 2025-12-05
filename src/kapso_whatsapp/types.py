"""
Kapso WhatsApp SDK Type Definitions

Pydantic v2 models for WhatsApp messages, templates, webhooks, and API responses.
Provides runtime validation, serialization, and IDE support.

Ported from flowers-backend with Pydantic upgrade and TypeScript SDK alignment.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Configuration
# =============================================================================


class ClientConfig(BaseModel):
    """WhatsApp client configuration."""

    model_config = ConfigDict(frozen=True)

    access_token: str | None = Field(default=None, description="Meta access token for Graph API")
    kapso_api_key: str | None = Field(default=None, description="Kapso API key for proxy")
    base_url: str = Field(
        default="https://graph.facebook.com",
        description="Base URL (Meta Graph or Kapso proxy)",
    )
    graph_version: str = Field(default="v23.0", description="Graph API version")
    timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_backoff: float = Field(default=1.0, ge=0.1, le=10.0, description="Retry backoff multiplier")

    @field_validator("access_token", "kapso_api_key", mode="before")
    @classmethod
    def validate_auth(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v


# =============================================================================
# Common Types
# =============================================================================


class MessageType(str, Enum):
    """WhatsApp message types."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    REACTION = "reaction"
    BUTTON = "button"
    ORDER = "order"
    UNKNOWN = "unknown"


class MessageDirection(str, Enum):
    """Message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    """Message delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    """Kapso message processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Message Input Types (for sending)
# =============================================================================


class TextMessageInput(BaseModel):
    """Input for sending a text message."""

    model_config = ConfigDict(populate_by_name=True)

    phone_number_id: str = Field(..., description="WhatsApp Business phone number ID")
    to: str = Field(..., description="Recipient phone number (E.164 format)")
    body: str = Field(..., min_length=1, max_length=4096, description="Message text")
    preview_url: bool = Field(default=False, description="Enable URL preview")


class MediaInput(BaseModel):
    """Media attachment (by ID or link)."""

    id: str | None = Field(default=None, description="Media ID from upload")
    link: str | None = Field(default=None, description="Public URL to media")
    caption: str | None = Field(default=None, max_length=1024, description="Media caption")
    filename: str | None = Field(default=None, description="Filename for documents")
    voice: bool | None = Field(default=None, description="Set to true for audio to play as voice note")

    @field_validator("link", mode="after")
    @classmethod
    def validate_has_source(cls, v: str | None, info: Any) -> str | None:
        if v is None and info.data.get("id") is None:
            raise ValueError("Either 'id' or 'link' must be provided")
        return v


class ImageMessageInput(BaseModel):
    """Input for sending an image message."""

    phone_number_id: str
    to: str
    image: MediaInput


class VideoMessageInput(BaseModel):
    """Input for sending a video message."""

    phone_number_id: str
    to: str
    video: MediaInput


class AudioMessageInput(BaseModel):
    """Input for sending an audio message."""

    phone_number_id: str
    to: str
    audio: MediaInput


class DocumentMessageInput(BaseModel):
    """Input for sending a document message."""

    phone_number_id: str
    to: str
    document: MediaInput


class StickerMessageInput(BaseModel):
    """Input for sending a sticker message."""

    phone_number_id: str
    to: str
    sticker: MediaInput


class LocationInput(BaseModel):
    """Geographic location."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)


class LocationMessageInput(BaseModel):
    """Input for sending a location message."""

    phone_number_id: str
    to: str
    location: LocationInput


class ReactionInput(BaseModel):
    """Message reaction."""

    message_id: str = Field(..., description="ID of message to react to")
    emoji: str = Field(..., max_length=10, description="Emoji reaction (empty to remove)")


class ReactionMessageInput(BaseModel):
    """Input for sending a reaction."""

    phone_number_id: str
    to: str
    reaction: ReactionInput


class ReplyContext(BaseModel):
    """Context for replying to a specific message."""

    message_id: str = Field(..., description="ID of the message to reply to")


# =============================================================================
# Contact Types
# =============================================================================


class ContactPhone(BaseModel):
    """Contact phone number."""

    phone: str
    type: Literal["CELL", "MAIN", "IPHONE", "HOME", "WORK"] = "CELL"
    wa_id: str | None = Field(default=None, alias="waId")


class ContactEmail(BaseModel):
    """Contact email address."""

    email: str
    type: Literal["HOME", "WORK"] = "WORK"


class ContactName(BaseModel):
    """Contact name details."""

    formatted_name: str = Field(..., alias="formattedName")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    middle_name: str | None = Field(default=None, alias="middleName")
    prefix: str | None = None
    suffix: str | None = None


class ContactAddress(BaseModel):
    """Contact address."""

    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    country_code: str | None = Field(default=None, alias="countryCode")
    type: Literal["HOME", "WORK"] = "HOME"


class ContactOrg(BaseModel):
    """Contact organization."""

    company: str | None = None
    department: str | None = None
    title: str | None = None


class ContactUrl(BaseModel):
    """Contact URL."""

    url: str
    type: Literal["HOME", "WORK"] = "WORK"


class Contact(BaseModel):
    """Contact card."""

    model_config = ConfigDict(populate_by_name=True)

    name: ContactName
    phones: list[ContactPhone] | None = None
    emails: list[ContactEmail] | None = None
    addresses: list[ContactAddress] | None = None
    org: ContactOrg | None = None
    urls: list[ContactUrl] | None = None
    birthday: str | None = None


class ContactsMessageInput(BaseModel):
    """Input for sending contact cards."""

    phone_number_id: str
    to: str
    contacts: list[Contact]


# =============================================================================
# Interactive Message Types
# =============================================================================


class Button(BaseModel):
    """Interactive reply button."""

    id: str = Field(..., max_length=256)
    title: str = Field(..., max_length=20)


class InteractiveHeader(BaseModel):
    """Interactive message header."""

    type: Literal["text", "image", "video", "document"]
    text: str | None = None
    image: MediaInput | None = None
    video: MediaInput | None = None
    document: MediaInput | None = None


class InteractiveButtonsInput(BaseModel):
    """Input for sending interactive button message."""

    phone_number_id: str
    to: str
    body_text: str = Field(..., max_length=1024, alias="bodyText")
    buttons: list[Button] = Field(..., min_length=1, max_length=3)
    header: InteractiveHeader | None = None
    header_text: str | None = Field(default=None, max_length=60, alias="headerText")
    footer_text: str | None = Field(default=None, max_length=60, alias="footerText")


class ListRow(BaseModel):
    """Row in an interactive list."""

    id: str = Field(..., max_length=200)
    title: str = Field(..., max_length=24)
    description: str | None = Field(default=None, max_length=72)


class ListSection(BaseModel):
    """Section in an interactive list."""

    title: str = Field(..., max_length=24)
    rows: list[ListRow] = Field(..., min_length=1, max_length=10)


class InteractiveListInput(BaseModel):
    """Input for sending interactive list message."""

    model_config = ConfigDict(populate_by_name=True)

    phone_number_id: str
    to: str
    body_text: str = Field(..., max_length=1024, alias="bodyText")
    button_text: str = Field(..., max_length=20, alias="buttonText")
    sections: list[ListSection] = Field(..., min_length=1, max_length=10)
    header_text: str | None = Field(default=None, max_length=60, alias="headerText")
    footer_text: str | None = Field(default=None, max_length=60, alias="footerText")


class CtaUrlParameters(BaseModel):
    """CTA URL button parameters."""

    display_text: str = Field(..., max_length=35, alias="displayText")
    url: str


class InteractiveCtaUrlInput(BaseModel):
    """Input for sending CTA URL button message."""

    model_config = ConfigDict(populate_by_name=True)

    phone_number_id: str
    to: str
    body_text: str = Field(..., max_length=1024, alias="bodyText")
    parameters: CtaUrlParameters
    header: InteractiveHeader | None = None
    footer_text: str | None = Field(default=None, max_length=60, alias="footerText")


class FlowActionPayload(BaseModel):
    """Flow action payload."""

    screen: str
    data: dict[str, Any] | None = None


class FlowParameters(BaseModel):
    """Flow message parameters."""

    model_config = ConfigDict(populate_by_name=True)

    flow_id: str = Field(..., alias="flowId")
    flow_cta: str = Field(..., max_length=20, alias="flowCta")
    flow_token: str | None = Field(default=None, alias="flowToken")
    flow_action: Literal["navigate", "data_exchange"] = Field(default="navigate", alias="flowAction")
    flow_action_payload: FlowActionPayload | None = Field(default=None, alias="flowActionPayload")
    flow_message_version: str = Field(default="3", alias="flowMessageVersion")


class InteractiveFlowInput(BaseModel):
    """Input for sending flow message."""

    model_config = ConfigDict(populate_by_name=True)

    phone_number_id: str
    to: str
    body_text: str = Field(..., max_length=1024, alias="bodyText")
    parameters: FlowParameters
    header: InteractiveHeader | None = None
    footer_text: str | None = Field(default=None, max_length=60, alias="footerText")


# =============================================================================
# Template Types
# =============================================================================


class TemplateLanguage(BaseModel):
    """Template language specification."""

    code: str
    policy: Literal["deterministic"] = "deterministic"


class TemplateParameter(BaseModel):
    """Template parameter."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["text", "image", "video", "document", "currency", "date_time", "payload", "action"]
    text: str | None = None
    parameter_name: str | None = Field(default=None, alias="parameterName")
    image: MediaInput | None = None
    video: MediaInput | None = None
    document: MediaInput | None = None
    currency: dict[str, Any] | None = None
    date_time: dict[str, Any] | None = Field(default=None, alias="dateTime")
    payload: str | None = None
    action: dict[str, Any] | None = None


class TemplateComponent(BaseModel):
    """Template component for sending."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["header", "body", "button"]
    parameters: list[TemplateParameter] = Field(default_factory=list)
    sub_type: Literal["quick_reply", "url", "copy_code", "flow"] | None = Field(
        default=None, alias="subType"
    )
    index: int | str | None = None


class TemplateSendPayload(BaseModel):
    """Template payload for sending."""

    name: str
    language: TemplateLanguage | str
    components: list[TemplateComponent] = Field(default_factory=list)


class TemplateMessageInput(BaseModel):
    """Input for sending a template message."""

    phone_number_id: str
    to: str
    template: TemplateSendPayload


# =============================================================================
# API Response Types
# =============================================================================


class MessageContact(BaseModel):
    """Contact info in message response."""

    model_config = ConfigDict(populate_by_name=True)

    input: str
    wa_id: str = Field(..., alias="waId")


class MessageInfo(BaseModel):
    """Message info in response."""

    id: str
    message_status: str | None = Field(default=None, alias="messageStatus")


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    model_config = ConfigDict(populate_by_name=True)

    messaging_product: str = Field(..., alias="messagingProduct")
    contacts: list[MessageContact] = Field(default_factory=list)
    messages: list[MessageInfo] = Field(default_factory=list)

    @property
    def message_id(self) -> str | None:
        """Get the first message ID."""
        return self.messages[0].id if self.messages else None


class MediaUploadResponse(BaseModel):
    """Response from media upload."""

    id: str


class MediaMetadata(BaseModel):
    """Media metadata response."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    mime_type: str = Field(..., alias="mimeType")
    sha256: str
    file_size: int = Field(..., alias="fileSize")
    messaging_product: str = Field(default="whatsapp", alias="messagingProduct")


# =============================================================================
# Webhook Types
# =============================================================================


class WebhookMessageText(BaseModel):
    """Text content in webhook message."""

    body: str


class WebhookMessageMedia(BaseModel):
    """Media content in webhook message."""

    id: str
    mime_type: str | None = Field(default=None, alias="mimeType")
    sha256: str | None = None
    caption: str | None = None
    filename: str | None = None


class WebhookMessageLocation(BaseModel):
    """Location content in webhook message."""

    latitude: float
    longitude: float
    name: str | None = None
    address: str | None = None


class WebhookInteractiveReply(BaseModel):
    """Interactive button/list reply."""

    id: str
    title: str


class WebhookInteractive(BaseModel):
    """Interactive response in webhook."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["button_reply", "list_reply", "nfm_reply"]
    button_reply: WebhookInteractiveReply | None = Field(default=None, alias="buttonReply")
    list_reply: WebhookInteractiveReply | None = Field(default=None, alias="listReply")
    nfm_reply: dict[str, Any] | None = Field(default=None, alias="nfmReply")


class WebhookButton(BaseModel):
    """Quick reply button response."""

    text: str
    payload: str


class WebhookMessage(BaseModel):
    """Parsed webhook message."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_: str = Field(..., alias="from")
    timestamp: str
    type: MessageType

    # Type-specific content
    text: WebhookMessageText | None = None
    image: WebhookMessageMedia | None = None
    video: WebhookMessageMedia | None = None
    audio: WebhookMessageMedia | None = None
    document: WebhookMessageMedia | None = None
    sticker: WebhookMessageMedia | None = None
    location: WebhookMessageLocation | None = None
    contacts: list[Contact] | None = None
    interactive: WebhookInteractive | None = None
    button: WebhookButton | None = None

    # Context
    context: dict[str, Any] | None = None

    # Kapso extensions
    direction: MessageDirection = MessageDirection.INBOUND
    kapso: dict[str, Any] | None = None


class WebhookStatusConversation(BaseModel):
    """Conversation info in status webhook."""

    id: str
    origin: dict[str, str] | None = None
    expiration_timestamp: str | None = Field(default=None, alias="expirationTimestamp")


class WebhookStatusPricing(BaseModel):
    """Pricing info in status webhook."""

    model_config = ConfigDict(populate_by_name=True)

    billable: bool
    pricing_model: str = Field(..., alias="pricingModel")
    category: str


class WebhookStatusError(BaseModel):
    """Error in status webhook."""

    code: int
    title: str
    message: str | None = None
    error_data: dict[str, Any] | None = Field(default=None, alias="errorData")


class WebhookStatus(BaseModel):
    """Message delivery status from webhook."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: MessageStatus
    timestamp: str
    recipient_id: str = Field(..., alias="recipientId")
    conversation: WebhookStatusConversation | None = None
    pricing: WebhookStatusPricing | None = None
    errors: list[WebhookStatusError] | None = None


class WebhookEvents(BaseModel):
    """Parsed webhook events container."""

    messages: list[WebhookMessage] = Field(default_factory=list)
    statuses: list[WebhookStatus] = Field(default_factory=list)
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    calls: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Kapso Proxy Types
# =============================================================================


class MediaData(BaseModel):
    """Media file information from Kapso."""

    model_config = ConfigDict(populate_by_name=True)

    url: str | None = None
    filename: str | None = None
    content_type: str | None = Field(default=None, alias="contentType")
    byte_size: int | None = Field(default=None, alias="byteSize")


class KapsoMessageFields(BaseModel):
    """Kapso extension fields for messages."""

    model_config = ConfigDict(populate_by_name=True)

    direction: MessageDirection | None = None
    status: MessageStatus | None = None
    processing_status: ProcessingStatus | None = Field(default=None, alias="processingStatus")
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    has_media: bool | None = Field(default=None, alias="hasMedia")
    media_url: str | None = Field(default=None, alias="mediaUrl")
    media_data: MediaData | None = Field(default=None, alias="mediaData")
    contact_name: str | None = Field(default=None, alias="contactName")
    whatsapp_conversation_id: str | None = Field(default=None, alias="whatsappConversationId")
    flow_response: dict[str, Any] | None = Field(default=None, alias="flowResponse")
    flow_token: str | None = Field(default=None, alias="flowToken")
    flow_name: str | None = Field(default=None, alias="flowName")
    content: str | None = None
    order_text: str | None = Field(default=None, alias="orderText")
    message_type_data: dict[str, Any] | None = Field(default=None, alias="messageTypeData")


class MessageContext(BaseModel):
    """Reply context for a message."""

    model_config = ConfigDict(populate_by_name=True)

    from_: str | None = Field(default=None, alias="from")
    id: str | None = None
    referred_product: dict[str, Any] | None = Field(default=None, alias="referredProduct")


class InteractiveResponseButton(BaseModel):
    """Button reply in interactive response."""

    id: str
    title: str


class InteractiveResponseList(BaseModel):
    """List reply in interactive response."""

    id: str
    title: str
    description: str | None = None


class InteractiveResponseNfm(BaseModel):
    """Native Flow Message reply."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    response_json: str | None = Field(default=None, alias="responseJson")
    body: str | None = None


class InteractiveResponse(BaseModel):
    """Interactive message response (for inbound interactive replies)."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["button_reply", "list_reply", "nfm_reply"] | None = None
    button_reply: InteractiveResponseButton | None = Field(default=None, alias="buttonReply")
    list_reply: InteractiveResponseList | None = Field(default=None, alias="listReply")
    nfm_reply: InteractiveResponseNfm | None = Field(default=None, alias="nfmReply")


class OrderMessageResponse(BaseModel):
    """Order message content."""

    model_config = ConfigDict(populate_by_name=True)

    catalog_id: str | None = Field(default=None, alias="catalogId")
    product_items: list[dict[str, Any]] | None = Field(default=None, alias="productItems")
    order_text: str | None = Field(default=None, alias="orderText")


class WhatsAppMessageResponse(BaseModel):
    """
    WhatsApp message from List Messages API.

    Represents both inbound and outbound messages with all type-specific
    content and Kapso extensions.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    timestamp: str
    type: MessageType

    # Direction-specific fields
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None

    # Reply context
    context: MessageContext | None = None

    # Type-specific content (only one will be present based on type)
    text: WebhookMessageText | None = None
    image: WebhookMessageMedia | None = None
    video: WebhookMessageMedia | None = None
    audio: WebhookMessageMedia | None = None
    document: WebhookMessageMedia | None = None
    sticker: WebhookMessageMedia | None = None
    location: WebhookMessageLocation | None = None
    contacts: list[Contact] | None = None
    order: OrderMessageResponse | None = None
    interactive: InteractiveResponse | None = None
    template: dict[str, Any] | None = None
    reaction: ReactionInput | None = None

    # Kapso extensions
    kapso: KapsoMessageFields | None = None


class PagingCursors(BaseModel):
    """Pagination cursors."""

    before: str | None = None
    after: str | None = None


class Paging(BaseModel):
    """Pagination info."""

    cursors: PagingCursors = Field(default_factory=PagingCursors)
    next: str | None = None
    previous: str | None = None


class ListMessagesResponse(BaseModel):
    """Response from List Messages API."""

    data: list[WhatsAppMessageResponse]
    paging: Paging = Field(default_factory=Paging)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    data: list[T]
    paging: Paging = Field(default_factory=Paging)


class ConversationKapso(BaseModel):
    """Kapso-specific conversation metadata extension."""

    model_config = ConfigDict(populate_by_name=True)

    contact_name: str | None = Field(default=None, alias="contactName", description="Contact display name")
    messages_count: int | None = Field(default=None, alias="messagesCount", description="Total message count")
    last_message_id: str | None = Field(default=None, alias="lastMessageId", description="WhatsApp message ID of last message")
    last_message_type: str | None = Field(default=None, alias="lastMessageType", description="Type of last message")
    last_message_timestamp: datetime | None = Field(default=None, alias="lastMessageTimestamp", description="Timestamp of last message")
    last_message_text: str | None = Field(default=None, alias="lastMessageText", description="Text content of last message")
    last_inbound_at: datetime | None = Field(default=None, alias="lastInboundAt", description="Timestamp of last inbound message")
    last_outbound_at: datetime | None = Field(default=None, alias="lastOutboundAt", description="Timestamp of last outbound message")


class Conversation(BaseModel):
    """WhatsApp conversation with Kapso extensions."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Conversation ID (UUID)")
    phone_number: str = Field(..., alias="phoneNumber", description="Contact's phone number (normalized)")
    status: Literal["active", "ended"] = Field(default="active", description="Conversation status")
    last_active_at: datetime | None = Field(default=None, alias="lastActiveAt", description="Last activity timestamp")
    created_at: datetime | None = Field(default=None, alias="createdAt", description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, alias="updatedAt", description="Last update timestamp")
    whatsapp_config_id: str | None = Field(default=None, alias="whatsappConfigId", description="WhatsApp configuration ID (UUID)")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")
    phone_number_id: str = Field(..., alias="phoneNumberId", description="WhatsApp Business Phone Number ID")
    kapso: ConversationKapso | None = Field(default=None, description="Kapso-specific conversation metadata")


class KapsoContact(BaseModel):
    """Kapso contact."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    wa_id: str = Field(..., alias="waId")
    phone_number_id: str = Field(..., alias="phoneNumberId")
    name: str | None = None
    customer_id: str | None = Field(default=None, alias="customerId")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class Call(BaseModel):
    """Kapso call record."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    phone_number_id: str = Field(..., alias="phoneNumberId")
    from_: str = Field(..., alias="from")
    to: str
    direction: Literal["INBOUND", "OUTBOUND"]
    status: str
    duration: int | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
