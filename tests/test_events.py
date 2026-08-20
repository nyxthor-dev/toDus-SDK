import pytest
import time
from todus.events import EventBus
from todus.events.filters import Filter, build_filter


class TestEventBus:
    def test_subscribe_and_dispatch(self):
        bus = EventBus()
        received = []
        bus.subscribe("message", lambda e: received.append(e))
        bus.dispatch("message", {"body": "hola"})
        assert len(received) == 1
        assert received[0]["body"] == "hola"

    def test_decorator(self):
        bus = EventBus()
        received = []

        @bus.on("message")
        def handler(evt):
            received.append(evt)

        bus.dispatch("message", {"body": "test"})
        assert len(received) == 1

    def test_priority_order(self):
        bus = EventBus()
        order = []
        bus.subscribe("msg", lambda e: order.append("low"), priority=0)
        bus.subscribe("msg", lambda e: order.append("high"), priority=10)
        bus.dispatch("msg", {})
        assert order == ["high", "low"]

    def test_stop_on_true(self):
        bus = EventBus()
        order = []
        bus.subscribe("msg", lambda e: (order.append("first"), True)[1], priority=10)
        bus.subscribe("msg", lambda e: order.append("second"), priority=0)
        bus.dispatch("msg", {})
        assert order == ["first"]

    def test_wildcard(self):
        bus = EventBus()
        received = []
        bus.subscribe("*", lambda e: received.append(e.get("_event_type")))
        bus.dispatch("message", {})
        bus.dispatch("presence", {})
        assert received == ["message", "presence"]

    def test_unsubscribe(self):
        bus = EventBus()
        def h(e): pass
        bus.subscribe("msg", h)
        assert bus.unsubscribe("msg", h) is True
        assert bus.unsubscribe("msg", h) is False

    def test_clear_specific(self):
        bus = EventBus()
        bus.subscribe("a", lambda e: None)
        bus.subscribe("b", lambda e: None)
        bus.clear("a")
        assert bus._handlers.get("a") is None
        assert bus._handlers.get("b") is not None

    def test_clear_all(self):
        bus = EventBus()
        bus.subscribe("a", lambda e: None)
        bus.subscribe("b", lambda e: None)
        bus.clear()
        assert len(bus._handlers) == 0

    def test_handler_exception_doesnt_break(self):
        bus = EventBus()
        received = []
        bus.subscribe("msg", lambda e: 1 / 0, priority=10)
        bus.subscribe("msg", lambda e: received.append("ok"), priority=0)
        bus.dispatch("msg", {})
        assert received == ["ok"]

    def test_no_handlers_no_error(self):
        bus = EventBus()
        bus.dispatch("nonexistent", {})  # should not raise


class TestFilters:
    def test_from_phone_match(self):
        f = Filter(from_phone="5354123456")
        assert f.matches({"from": "5354123456@im.todus.cu"}) is True
        assert f.matches({"from": "5398765432@im.todus.cu"}) is False

    def test_from_phone_with_resource(self):
        f = Filter(from_phone="5354123456")
        assert f.matches({"from": "grp1@muclight.im.todus.cu/5354123456"}) is True

    def test_contains_keyword(self):
        f = Filter(contains_keyword="hola")
        assert f.matches({"body": "hola mundo"}) is True
        assert f.matches({"body": "chao"}) is False

    def test_is_group(self):
        f = Filter(is_group=True)
        assert f.matches({"is_group": True}) is True
        assert f.matches({"is_group": False}) is False

    def test_group_id(self):
        f = Filter(group_id="grp123")
        assert f.matches({"group_id": "grp123"}) is True
        assert f.matches({"group_id": "other"}) is False

    def test_regex(self):
        f = Filter(regex=r"^/cmd")
        assert f.matches({"body": "/cmd start"}) is True
        assert f.matches({"body": "normal"}) is False

    def test_custom(self):
        f = Filter(custom=lambda e: e.get("priority", 0) > 5)
        assert f.matches({"priority": 10}) is True
        assert f.matches({"priority": 3}) is False

    def test_combined_filters(self):
        f = Filter(from_phone="5354123456", contains_keyword="hola")
        assert f.matches({"from": "5354123456@im.todus.cu", "body": "hola"}) is True
        assert f.matches({"from": "5354123456@im.todus.cu", "body": "chao"}) is False
        assert f.matches({"from": "5399999999@im.todus.cu", "body": "hola"}) is False

    def test_build_filter(self):
        fn = build_filter(contains_keyword="test")
        assert fn({"body": "test pass"}) is True
        assert fn({"body": "nope"}) is False

    def test_filter_with_decorator(self):
        bus = EventBus()
        received = []

        @bus.on("message", from_phone="5354123456")
        def on_my_msg(evt):
            received.append(evt)

        bus.dispatch("message", {"from": "5354123456@im.todus.cu", "body": "hola"})
        bus.dispatch("message", {"from": "5398765432@im.todus.cu", "body": "hola"})
        assert len(received) == 1
        assert received[0]["from"] == "5354123456@im.todus.cu"
