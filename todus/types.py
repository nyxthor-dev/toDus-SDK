"""Tipos y enumeraciones de ToDus."""

from enum import IntEnum, StrEnum


class FileType(IntEnum):
    """Tipos de archivo soportados por ToDus.

    Códigos del protocolo oficial:
    TYPE_FILE=0, TYPE_VOICE=1, TYPE_AUDIO=2, TYPE_VIDEO=3,
    TYPE_PICTURE=4, TYPE_PROFILE=5. ``PROFILE_THUMBNAIL`` es una
    extensión propia del SDK (no existe en el protocolo oficial).
    """
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


class ButtonSize(StrEnum):
    """Tamaños de botón interactivo (valores oficiales).

    El protocolo usa ``0.4`` (medio) y ``0.82`` (completo). El valor ``0.5``
    no existe en el protocolo oficial.
    """
    FULL = "0.82"
    MID = "0.4"
    # Alias deprecado (el valor correcto es 0.4)
    HALF = "0.4"


class ButtonCommand(StrEnum):
    """Tipos de comando para botones interactivos (valores oficiales).

    El protocolo define: ``cmd_type_send``, ``cmd_open_web``,
    ``cmd_copy_to_clipboard``, ``cmd_add_shortcut`` y
    ``cmd_open_app_screen``.
    """
    SEND = "cmd_type_send"
    OPEN_WEB = "cmd_open_web"
    COPY_TO_CLIPBOARD = "cmd_copy_to_clipboard"
    ADD_SHORTCUT = "cmd_add_shortcut"
    OPEN_APP_SCREEN = "cmd_open_app_screen"
