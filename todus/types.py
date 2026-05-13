from enum import Enum, IntEnum


class FileType(IntEnum):
    FILE = 0
    VOICE = 1
    AUDIO = 2
    VIDEO = 3
    PICTURE = 4
    PROFILE = 5
    PROFILE_THUMBNAIL = 6


class ChatState(str, Enum):
    COMPOSING = "composing"
    PAUSED = "paused"
    ACTIVE = "active"
    GONE = "gone"
    INACTIVE = "inactive"


class MessageType(str, Enum):
    CHAT = "chat"
    GROUPCHAT = "groupchat"
    ERROR = "error"
    HEADLINE = "headline"
    NORMAL = "normal"


class PresenceShow(str, Enum):
    CHAT = "chat"
    AWAY = "away"
    XA = "xa"
    DND = "dnd"
    
