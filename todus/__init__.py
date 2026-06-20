"""ToDus Python Library - Cliente XMPP/HTTP para ToDus."""

from .client import ToDusClient, ToDusClient2
from .group import GroupClient, GroupRole, GroupEvent
from .types import FileType, ChatState, MessageType, PresenceShow, ButtonSize, ButtonCommand
from .errors import (
    ToDusError,
    AuthenticationError,
    TokenExpiredError,
    ConnectionLostError,
    MessageError,
    UploadError,
    ParseError,
    RateLimitError,
    StanzaError,
    GroupError,
)
from .util import normalize_phone, build_jid, generate_token, jwt_decode_payload, timestamp_ms, format_size
from .parser import IncrementalParser, parse_tdack

__version__ = "1.3.3"
__all__ = [
    "ToDusClient",
    "ToDusClient2",
    "GroupClient",
    "GroupRole",
    "GroupEvent",
    "FileType",
    "ChatState",
    "MessageType",
    "PresenceShow",
    "ButtonSize",
    "ButtonCommand",
    "ToDusError",
    "AuthenticationError",
    "TokenExpiredError",
    "ConnectionLostError",
    "MessageError",
    "UploadError",
    "ParseError",
    "RateLimitError",
    "StanzaError",
    "GroupError",
    "normalize_phone",
    "build_jid",
    "generate_token",
    "jwt_decode_payload",
    "timestamp_ms",
    "format_size",
    "IncrementalParser",
    "parse_tdack",
]