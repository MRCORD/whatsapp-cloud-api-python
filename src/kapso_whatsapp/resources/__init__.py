"""WhatsApp API Resources."""

from .calls import CallsResource
from .contacts import ContactsResource
from .conversations import ConversationsResource
from .flows import FlowsResource
from .media import MediaResource
from .messages import MessagesResource
from .phone_numbers import PhoneNumbersResource
from .templates import TemplatesResource

__all__ = [
    "MessagesResource",
    "MediaResource",
    "TemplatesResource",
    "PhoneNumbersResource",
    "FlowsResource",
    "ConversationsResource",
    "ContactsResource",
    "CallsResource",
]
