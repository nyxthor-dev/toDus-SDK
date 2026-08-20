import time
import tempfile
import os
import pytest
from todus.cache import MessageStore, Message, MessageStatus


class TestMessage:
    def test_defaults(self):
        m = Message(msg_id="m1", to="53@im.todus.cu", body="hola")
        assert m.status == MessageStatus.PENDING
        assert m.retry_count == 0
        assert m.metadata == {}
        assert m.created_at > 0

    def test_to_dict_roundtrip(self):
        m = Message(msg_id="m1", to="53@im.todus.cu", body="hola", metadata={"key": "val"})
        d = m.to_dict()
        m2 = Message.from_dict(d)
        assert m2.msg_id == "m1"
        assert m2.body == "hola"
        assert m2.metadata == {"key": "val"}


class TestMessageStore:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.store = MessageStore(self.tmpfile)

    def teardown_method(self):
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_add_and_get(self):
        m = Message(msg_id="m1", to="53@im.todus.cu", body="hola")
        self.store.add(m)
        retrieved = self.store.get("m1")
        assert retrieved is not None
        assert retrieved.body == "hola"

    def test_get_nonexistent(self):
        assert self.store.get("no_existe") is None

    def test_get_by_status(self):
        self.store.add(Message(msg_id="m1", to="a", body="1"))
        self.store.add(Message(msg_id="m2", to="b", body="2", status=MessageStatus.SENT))
        pending = self.store.get_by_status(MessageStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].msg_id == "m1"

    def test_update_status(self):
        self.store.add(Message(msg_id="m1", to="a", body="x"))
        self.store.update_status("m1", MessageStatus.SENT)
        m = self.store.get("m1")
        assert m.status == MessageStatus.SENT
        assert m.sent_at is not None

    def test_update_to_read(self):
        self.store.add(Message(msg_id="m1", to="a", body="x"))
        self.store.update_status("m1", MessageStatus.READ)
        m = self.store.get("m1")
        assert m.status == MessageStatus.READ
        assert m.read_at is not None

    def test_update_to_failed(self):
        self.store.add(Message(msg_id="m1", to="a", body="x"))
        self.store.update_status("m1", MessageStatus.FAILED, error="timeout")
        m = self.store.get("m1")
        assert m.status == MessageStatus.FAILED
        assert m.last_error == "timeout"

    def test_increment_retry(self):
        self.store.add(Message(msg_id="m1", to="a", body="x"))
        self.store.increment_retry("m1")
        self.store.increment_retry("m1")
        m = self.store.get("m1")
        assert m.retry_count == 2

    def test_delete(self):
        self.store.add(Message(msg_id="m1", to="a", body="x"))
        assert self.store.delete("m1") is True
        assert self.store.get("m1") is None

    def test_stats(self):
        self.store.add(Message(msg_id="m1", to="a", body="1"))
        self.store.add(Message(msg_id="m2", to="b", body="2", status=MessageStatus.SENT))
        self.store.add(Message(msg_id="m3", to="c", body="3", status=MessageStatus.SENT))
        stats = self.store.get_stats()
        assert stats.get("pending") == 1
        assert stats.get("sent") == 2

    def test_clear_old(self):
        old_ts = time.time() - (31 * 86400)
        m = Message(msg_id="old", to="a", body="old", status=MessageStatus.READ)
        m.created_at = old_ts
        self.store.add(m)
        self.store.add(Message(msg_id="new", to="a", body="new", status=MessageStatus.READ))
        deleted = self.store.clear_old(days=30)
        assert deleted == 1
        assert self.store.get("old") is None
        assert self.store.get("new") is not None
