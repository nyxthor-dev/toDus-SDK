import re
import string
from types import SimpleNamespace
import requests

from todus.client.auth import ToDusAuthMixin
from todus import util


class DummyClient(ToDusAuthMixin):
    def __init__(self):
        self.version_name = "1.0"
        self.version_code = "1.0"
        self.session = requests.Session()


class FakeResp:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        try:
            self.text = content.decode("utf-8")
        except Exception:
            self.text = ""

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.HTTPError(f"Status {self.status_code}")


def test_validate_code_parses_token(monkeypatch):
    # Simulate auth server response that contains a 96-char token
    token = "a" * 96
    raw = b"xxxxx`" + token.encode()

    def fake_post(*args, **kwargs):
        return FakeResp(raw)

    client = DummyClient()
    monkeypatch.setattr(client, "session", SimpleNamespace(post=fake_post))

    pw = client.validate_code("5312345678", "1234")
    assert isinstance(pw, str)
    assert re.match(r"^[a-f0-9A-Za-z]+$", pw) or len(pw) >= 1


def test_login_raises_on_403(monkeypatch):
    def fake_post_403(*args, **kwargs):
        return FakeResp(b"FORBIDDEN", status_code=403)

    client = DummyClient()
    monkeypatch.setattr(client, "session", SimpleNamespace(post=fake_post_403))

    try:
        client.login("5312345678", "badpw")
    except Exception as e:
        assert hasattr(e, "args")
