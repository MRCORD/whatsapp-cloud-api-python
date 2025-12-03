"""
Kapso WhatsApp SDK

A Python SDK for the WhatsApp Business Cloud API with Kapso proxy support.

Provides:
- Async HTTP client with retry logic
- Full messaging capabilities (text, media, templates, interactive)
- Webhook signature verification and normalization
- Flow server-side handling
- Kapso proxy integration (conversations, contacts, calls)

Example:
    >>> from kapso_whatsapp import WhatsAppClient
    >>> async with WhatsAppClient(access_token="your_token") as client:
    ...     await client.messages.send_text(
    ...         phone_number_id="123456",
    ...         to="+15551234567",
    ...         body="Hello!"
    ...     )
"""

from .client import WhatsAppClient
from .exceptions import (
    AuthenticationError,
    ErrorCategory,
    KapsoProxyRequiredError,
    MessageWindowError,
    NetworkError,
    RateLimitError,
    RetryAction,
    TimeoutError,
    ValidationError,
    WhatsAppAPIError,
    categorize_error,
)
from .kapso import (
    KAPSO_MESSAGE_FIELDS,
    KapsoMessageField,
    build_kapso_fields,
    build_kapso_message_fields,
)
from .types import (
    # Message inputs
    AudioMessageInput,
    Button,
    # Kapso proxy types
    Call,
    # Configuration
    ClientConfig,
    Contact,
    ContactAddress,
    ContactEmail,
    ContactName,
    ContactOrg,
    ContactPhone,
    ContactsMessageInput,
    ContactUrl,
    Conversation,
    ConversationKapso,
    CtaUrlParameters,
    DocumentMessageInput,
    FlowActionPayload,
    FlowParameters,
    ImageMessageInput,
    InteractiveButtonsInput,
    InteractiveCtaUrlInput,
    InteractiveFlowInput,
    InteractiveHeader,
    InteractiveListInput,
    # List Messages response types
    InteractiveResponse,
    InteractiveResponseButton,
    InteractiveResponseList,
    InteractiveResponseNfm,
    KapsoContact,
    KapsoMessageFields,
    ListMessagesResponse,
    ListRow,
    ListSection,
    LocationInput,
    LocationMessageInput,
    MediaData,
    MediaInput,
    # Responses
    MediaMetadata,
    MediaUploadResponse,
    MessageContact,
    MessageContext,
    # Enums
    MessageDirection,
    MessageInfo,
    MessageStatus,
    MessageType,
    OrderMessageResponse,
    PaginatedResponse,
    Paging,
    PagingCursors,
    # Processing status
    ProcessingStatus,
    ReactionInput,
    ReactionMessageInput,
    ReplyContext,
    SendMessageResponse,
    StickerMessageInput,
    TemplateComponent,
    TemplateLanguage,
    TemplateMessageInput,
    TemplateParameter,
    TemplateSendPayload,
    TextMessageInput,
    VideoMessageInput,
    # Webhook types
    WebhookButton,
    WebhookEvents,
    WebhookInteractive,
    WebhookInteractiveReply,
    WebhookMessage,
    WebhookMessageLocation,
    WebhookMessageMedia,
    WebhookMessageText,
    WebhookStatus,
    WebhookStatusConversation,
    WebhookStatusError,
    WebhookStatusPricing,
    WhatsAppMessageResponse,
)

__all__ = [
    # Client
    "WhatsAppClient",
    # Exceptions
    "WhatsAppAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "KapsoProxyRequiredError",
    "MessageWindowError",
    "ErrorCategory",
    "RetryAction",
    "categorize_error",
    # Kapso helpers
    "KAPSO_MESSAGE_FIELDS",
    "KapsoMessageField",
    "build_kapso_fields",
    "build_kapso_message_fields",
    # Configuration
    "ClientConfig",
    # Enums
    "MessageType",
    "MessageDirection",
    "MessageStatus",
    "ProcessingStatus",
    # Message inputs
    "TextMessageInput",
    "MediaInput",
    "ImageMessageInput",
    "VideoMessageInput",
    "AudioMessageInput",
    "DocumentMessageInput",
    "StickerMessageInput",
    "LocationInput",
    "LocationMessageInput",
    "ReactionInput",
    "ReactionMessageInput",
    "ReplyContext",
    "Button",
    "InteractiveHeader",
    "InteractiveButtonsInput",
    "ListRow",
    "ListSection",
    "InteractiveListInput",
    "CtaUrlParameters",
    "InteractiveCtaUrlInput",
    "FlowActionPayload",
    "FlowParameters",
    "InteractiveFlowInput",
    "Contact",
    "ContactName",
    "ContactPhone",
    "ContactEmail",
    "ContactAddress",
    "ContactOrg",
    "ContactUrl",
    "ContactsMessageInput",
    "TemplateLanguage",
    "TemplateParameter",
    "TemplateComponent",
    "TemplateSendPayload",
    "TemplateMessageInput",
    # Responses
    "MessageContact",
    "MessageInfo",
    "SendMessageResponse",
    "MediaUploadResponse",
    "MediaMetadata",
    # Webhook types
    "WebhookMessageText",
    "WebhookMessageMedia",
    "WebhookMessageLocation",
    "WebhookInteractiveReply",
    "WebhookInteractive",
    "WebhookButton",
    "WebhookMessage",
    "WebhookStatusConversation",
    "WebhookStatusPricing",
    "WebhookStatusError",
    "WebhookStatus",
    "WebhookEvents",
    # Kapso proxy types
    "KapsoMessageFields",
    "MediaData",
    "PagingCursors",
    "Paging",
    "PaginatedResponse",
    "Conversation",
    "ConversationKapso",
    "KapsoContact",
    "Call",
    # List Messages API types
    "WhatsAppMessageResponse",
    "ListMessagesResponse",
    "MessageContext",
    "InteractiveResponse",
    "InteractiveResponseButton",
    "InteractiveResponseList",
    "InteractiveResponseNfm",
    "OrderMessageResponse",
]

__version__ = "0.1.0"
