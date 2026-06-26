import re

from todus.events import EventBus, build_filter


def test_basic_message_filter_and_dispatch():
    bus = EventBus()
    seen = []

    @bus.on("message", from_phone="5312345678")
    def h1(evt):
        seen.append(("h1", evt.get("from"), evt.get("body")))

    msg = {"from": "5312345678", "body": "hola"}
    bus.dispatch("message", msg)
    assert seen == [("h1", "5312345678", "hola")]


def test_priority_and_stop_propagation():
    bus = EventBus()
    order = []

    @bus.on("message", priority=10)
    def first(evt):
        order.append("first")

    @bus.on("message", priority=5)
    def second(evt):
        order.append("second")
        return True

    @bus.on("message", priority=1)
    def third(evt):
        order.append("third")

    bus.dispatch("message", {"from": "X"})
    # second returns True -> stops, so 'third' should not run
    assert order == ["first", "second"]


def test_wildcard_handlers_receive_event_type():
    bus = EventBus()
    seen = []

    @bus.on("*")
    def wildcard(evt):
        # should receive _event_type tag
        seen.append(evt.get("_event_type"))

    bus.dispatch("message", {"from": "A"})
    bus.dispatch("presence", {"from": "B"})
    assert seen == ["message", "presence"]


def test_unsubscribe_and_clear():
    bus = EventBus()
    called = []

    def h(evt):
        called.append(True)

    bus.subscribe("message", h)
    bus.dispatch("message", {"from": "1"})
    assert called == [True]

    assert bus.unsubscribe("message", h) is True
    bus.dispatch("message", {"from": "1"})
    assert called == [True]

    # test clear
    def h2(evt):
        called.append(2)

    bus.subscribe("x", h2)
    bus.clear()
    bus.dispatch("x", {})
    assert 2 not in called


def test_regex_and_custom_filter():
    bus = EventBus()
    seen = []

    @bus.on("message", regex=r"hello")
    def r(evt):
        seen.append("r")

    @bus.on("message", custom=lambda e: e.get("score", 0) > 5)
    def c(evt):
        seen.append("c")

    bus.dispatch("message", {"body": "say hello world", "score": 10})
    assert seen == ["r", "c"]
