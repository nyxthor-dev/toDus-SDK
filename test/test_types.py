"""Tests para todus.types."""

from todus.types import (
    FileType,
    ChatState,
    MessageType,
    PresenceShow,
    ButtonSize,
    ButtonCommand,
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

    def test_is_int(self):
        assert isinstance(FileType.FILE, int)
        assert isinstance(FileType.PICTURE, int)

    def test_membership(self):
        assert 0 in FileType._value2member_map_
        assert 4 in FileType._value2member_map_
        assert 99 not in FileType._value2member_map_


class TestChatState:
    def test_values(self):
        assert ChatState.COMPOSING == "composing"
        assert ChatState.PAUSED == "paused"
        assert ChatState.ACTIVE == "active"
        assert ChatState.GONE == "gone"
        assert ChatState.INACTIVE == "inactive"

    def test_is_str(self):
        assert isinstance(ChatState.COMPOSING, str)


class TestMessageType:
    def test_values(self):
        assert MessageType.CHAT == "chat"
        assert MessageType.GROUPCHAT == "groupchat"
        assert MessageType.ERROR == "error"
        assert MessageType.HEADLINE == "headline"
        assert MessageType.NORMAL == "normal"


class TestPresenceShow:
    def test_values(self):
        assert PresenceShow.CHAT == "chat"
        assert PresenceShow.AWAY == "away"
        assert PresenceShow.XA == "xa"
        assert PresenceShow.DND == "dnd"


class TestButtonSize:
    def test_values(self):
        assert ButtonSize.FULL == "0.82"
        assert ButtonSize.HALF == "0.5"


class TestButtonCommand:
    def test_values(self):
        assert ButtonCommand.SEND == "cmd_type_send"
        assert ButtonCommand.URL == "cmd_type_url"
        assert ButtonCommand.COPY == "cmd_type_copy"
        assert ButtonCommand.CALL == "cmd_type_call"
