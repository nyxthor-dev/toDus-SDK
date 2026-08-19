"""Tests para EventBus filters."""
import pytest
from todus.events.filters import Filter, build_filter


class TestFilterFromPhone:
    """Tests para el filtro from_phone corregido."""

    def test_matches_plain_phone(self):
        f = Filter(from_phone="5312345678")
        evt = {"from": "5312345678@im.todus.cu", "body": "hola"}
        assert f.matches(evt) is True

    def test_matches_sender_phone(self):
        f = Filter(from_phone="5312345678")
        evt = {"from": "grupo@muclight.im.todus.cu/5312345678@im.todus.cu", "sender_phone": "5312345678"}
        assert f.matches(evt) is True

    def test_no_match_wrong_phone(self):
        f = Filter(from_phone="5312345678")
        evt = {"from": "5399999999@im.todus.cu", "body": "hola"}
        assert f.matches(evt) is False

    def test_no_match_empty(self):
        f = Filter(from_phone="5312345678")
        evt = {"from": "", "body": "hola"}
        assert f.matches(evt) is False

    def test_null_filter_passes(self):
        f = Filter()  # from_phone is None
        evt = {"from": "anyone@im.todus.cu", "body": "hola"}
        assert f.matches(evt) is True


class TestBuildFilter:
    def test_build_from_phone(self):
        fn = build_filter(from_phone="5312345678")
        evt = {"from": "5312345678@im.todus.cu", "body": "hola"}
        assert fn(evt) is True

    def test_build_keyword(self):
        fn = build_filter(contains_keyword="hola")
        assert fn({"body": "hola mundo"}) is True
        assert fn({"body": "chau"}) is False

    def test_build_regex(self):
        fn = build_filter(regex=r"^/cmd")
        assert fn({"body": "/cmd help"}) is True
        assert fn({"body": "texto /cmd"}) is False

    def test_build_is_group(self):
        fn = build_filter(is_group=True)
        assert fn({"is_group": True}) is True
        assert fn({"is_group": False}) is False
        assert fn({}) is False

    def test_build_group_id(self):
        fn = build_filter(group_id="abc123")
        assert fn({"group_id": "abc123"}) is True
        assert fn({"group_id": "other"}) is False

    def test_build_custom(self):
        fn = build_filter(custom=lambda e: len(e.get("body", "")) > 5)
        assert fn({"body": "123456"}) is True
        assert fn({"body": "123"}) is False

    def test_combined_filters(self):
        fn = build_filter(from_phone="53123", contains_keyword="hola")
        evt_ok = {"from": "53123@im.todus.cu", "body": "hola mundo"}
        evt_phone_fail = {"from": "53999@im.todus.cu", "body": "hola mundo"}
        evt_keyword_fail = {"from": "53123@im.todus.cu", "body": "chau"}
        assert fn(evt_ok) is True
        assert fn(evt_phone_fail) is False
        assert fn(evt_keyword_fail) is False
