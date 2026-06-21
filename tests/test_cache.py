"""Tests para Message Queue."""

import pytest
import tempfile
import time
from pathlib import Path
from todus.cache import MessageStore, Message, MessageStatus, MessageQueue


class TestMessageStore:
    """Tests para MessageStore."""

    @pytest.fixture
    def store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            yield MessageStore(db_path)

    def test_add_and_get(self, store):
        msg = Message(
            msg_id="msg1",
            to="5312345678@im.todus.cu",
            body="Hola",
            status=MessageStatus.PENDING
        )
        assert store.add(msg)
        
        retrieved = store.get("msg1")
        assert retrieved is not None
        assert retrieved.msg_id == "msg1"
        assert retrieved.body == "Hola"

    def test_get_by_status(self, store):
        for i in range(5):
            msg = Message(
                msg_id=f"msg{i}",
                to="5312345678@im.todus.cu",
                body=f"Test {i}",
                status=MessageStatus.PENDING
            )
            store.add(msg)
        
        pending = store.get_by_status(MessageStatus.PENDING)
        assert len(pending) == 5

    def test_update_status(self, store):
        msg = Message(msg_id="msg1", to="5312345678@im.todus.cu", body="Test")
        store.add(msg)
        
        assert store.update_status("msg1", MessageStatus.SENT)
        updated = store.get("msg1")
        assert updated.status == MessageStatus.SENT
        assert updated.sent_at is not None

    def test_increment_retry(self, store):
        msg = Message(msg_id="msg1", to="5312345678@im.todus.cu", body="Test", retry_count=0)
        store.add(msg)
        
        assert store.increment_retry("msg1")
        updated = store.get("msg1")
        assert updated.retry_count == 1


class TestMessageQueue:
    """Tests para MessageQueue."""

    @pytest.fixture
    def queue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = MessageStore(db_path)
            yield MessageQueue(store, auto_retry=False)

    def test_enqueue(self, queue):
        msg = queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")
        assert msg.msg_id == "msg1"
        assert msg.status == MessageStatus.PENDING

    def test_mark_sent(self, queue):
        queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")
        assert queue.mark_sent("msg1")
        
        msg = queue.store.get("msg1")
        assert msg.status == MessageStatus.SENT

    def test_mark_delivered(self, queue):
        queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")
        assert queue.mark_delivered("msg1")
        
        msg = queue.store.get("msg1")
        assert msg.status == MessageStatus.DELIVERED

    def test_mark_read(self, queue):
        queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")
        assert queue.mark_read("msg1")
        
        msg = queue.store.get("msg1")
        assert msg.status == MessageStatus.READ

    def test_callback_triggered(self, queue):
        callback_called = {"count": 0, "msg": None}
        
        def on_delivered(msg):
            callback_called["count"] += 1
            callback_called["msg"] = msg
        
        queue.register_callback("on_message_delivered", on_delivered)
        queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")
        queue.mark_delivered("msg1")
        
        assert callback_called["count"] == 1
        assert callback_called["msg"].msg_id == "msg1"

    def test_backoff_time_increases(self, queue):
        msg0 = Message(msg_id="m0", to="test", body="test", retry_count=0)
        msg1 = Message(msg_id="m1", to="test", body="test", retry_count=1)
        msg5 = Message(msg_id="m5", to="test", body="test", retry_count=5)
        
        t0 = queue.get_backoff_time(msg0)
        t1 = queue.get_backoff_time(msg1)
        t5 = queue.get_backoff_time(msg5)
        
        # Exponencial: 2^0=1, 2^1=2, 2^5=32
        assert t0 < t1 < t5
