"""Tipos y enumeraciones de ToDus."""

from enum import IntEnum, StrEnum


class FileType(IntEnum):
    """Tipos de archivo soportados por ToDus."""
    FILE = 0
    VOICE = 1
    AUDIO = 2
    VIDEO = 3
    PICTURE = 4
    PROFILE = 5
    PROFILE_THUMBNAIL = 6


class ChatState(StrEnum):
    """Estados de chat XEP-0085."""
    COMPOSING = "composing"
    PAUSED = "paused"
    ACTIVE = "active"
    GONE = "gone"
    INACTIVE = "inactive"


class MessageType(StrEnum):
    """Tipos de mensaje XMPP."""
    CHAT = "chat"
    GROUPCHAT = "groupchat"
    ERROR = "error"
    HEADLINE = "headline"
    NORMAL = "normal"


class PresenceShow(StrEnum):
    """Estados de presencia XMPP."""
    CHAT = "chat"
    AWAY = "away"
    XA = "xa"
    DND = "dnd"
