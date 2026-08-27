import pytest
from todus.types import FileType, ChatState, MessageType, PresenceShow, ButtonSize, ButtonCommand
from todus.errors import (
    ToDusError, AuthenticationError, TokenExpiredError, ConnectionLostError,
    MessageError, UploadError, ParseError, RateLimitError, StanzaError, GroupError,
)


class TestFileType:
    def test_values(self):
        assert FileType.FILE == 0
        assert FileType.VOICE == 1
        assert FileType.AUDIO == 2
        assert FileType.VIDEO == 3
        assert FileType.PICTURE == 4
        assert FileType.PROFILE == 5
        assert FileType.PROFILE_THUMBNAIL == 6

    def test_is_int_enum(self):
        assert isinstance(FileType.PICTURE, int)


class TestChatState:
    def test_values(self):
        assert ChatState.COMPOSING == "composing"
        assert ChatState.PAUSED == "paused"
        assert ChatState.ACTIVE == "active"
        assert ChatState.GONE == "gone"
        assert ChatState.INACTIVE == "inactive"


class TestMessageType:
    def test_values(self):
        assert MessageType.CHAT == "chat"
        assert MessageType.GROUPCHAT == "groupchat"
        assert MessageType.ERROR == "error"


class TestPresenceShow:
    def test_values(self):
        assert PresenceShow.CHAT == "chat"
        assert PresenceShow.AWAY == "away"
        assert PresenceShow.XA == "xa"
        assert PresenceShow.DND == "dnd"


class TestButtonSize:
    def test_values(self):
        # 0.4 (medio) y 0.82 (completo); 0.5 no existe
        assert ButtonSize.FULL == "0.82"
        assert ButtonSize.MID == "0.4"
        assert ButtonSize.HALF == "0.4"  # alias deprecado


class TestButtonCommand:
    def test_values(self):
        # Comandos reales del protocolo
        assert ButtonCommand.SEND == "cmd_type_send"
        assert ButtonCommand.OPEN_WEB == "cmd_open_web"
        assert ButtonCommand.COPY_TO_CLIPBOARD == "cmd_copy_to_clipboard"
        assert ButtonCommand.ADD_SHORTCUT == "cmd_add_shortcut"
        assert ButtonCommand.OPEN_APP_SCREEN == "cmd_open_app_screen"


class TestErrorHierarchy:
    def test_all_inherit_from_todus_error(self):
        assert issubclass(AuthenticationError, ToDusError)
        assert issubclass(TokenExpiredError, ToDusError)
        assert issubclass(ConnectionLostError, ToDusError)
        assert issubclass(MessageError, ToDusError)
        assert issubclass(UploadError, ToDusError)
        assert issubclass(ParseError, ToDusError)
        assert issubclass(RateLimitError, ToDusError)
        assert issubclass(StanzaError, ToDusError)
        assert issubclass(GroupError, ToDusError)

    def test_catch_with_base(self):
        with pytest.raises(ToDusError):
            raise AuthenticationError("fail")

    def test_message_preserved(self):
        err = UploadError("archivo muy grande")
        assert str(err) == "archivo muy grande"
