"""Tests para base client (handshake, XMPP, etc)."""
from unittest.mock import Mock, patch, MagicMock
import pytest
from todus.client.base import ToDusClientBase
from todus.errors import TokenExpiredError, ConnectionLostError


class TestXmppHandshake:
    """Tests para handshake XMPP."""

    def test_process_handshake_init_state(self):
        client = ToDusClientBase()
        sock = Mock()
        state = {"phase": "init"}
        response = "<?xml version='1.0'?><stream:stream><stream:features><es xmlns='x2'></stream:features>"
        authstr = b"test_auth"

        result = client._process_handshake(response, sock, authstr, "test_sid", state)
        assert result is True
        assert state["phase"] == "auth_sent"
        sock.send.assert_called_once()

    def test_process_handshake_auth_success(self):
        client = ToDusClientBase()
        sock = Mock()
        state = {"phase": "auth_sent"}
        response = "<ok xmlns='x2'/>"
        authstr = b"test_auth"

        result = client._process_handshake(response, sock, authstr, "test_sid", state)
        assert result is True
        assert state["phase"] == "restream"

    def test_process_handshake_auth_failure(self):
        client = ToDusClientBase()
        sock = Mock()
        state = {"phase": "auth_sent"}
        response = "<not-authorized/>"
        authstr = b"test_auth"

        with pytest.raises(TokenExpiredError):
            client._process_handshake(response, sock, authstr, "test_sid", state)

    def test_authstr_from_token_decodes_jwt(self):
        client = ToDusClientBase()
        # Token JWT fake (header.payload.sig)
        # payload: {"username": "5312345678"}
        import base64
        payload = base64.b64encode(b'{"username": "5312345678"}').decode().rstrip('=')
        token = f"header.{payload}.sig"

        phone, authstr = client._authstr_from_token(token)
        assert phone == "5312345678"
        assert isinstance(authstr, bytes)


class TestConnectionErrors:
    """Tests para manejo de errores de conexión."""

    def test_recv_all_returns_none_on_connection_close(self):
        client = ToDusClientBase()
        sock = Mock()
        sock.recv.side_effect = OSError("Connection closed")

        result = client._recv_all(sock)
        assert result is None

    def test_recv_all_returns_data_on_success(self):
        client = ToDusClientBase()
        sock = Mock()
        sock.recv.side_effect = [b"part1", b"part2", b""]

        result = client._recv_all(sock)
        assert result is not None
        assert "part1" in result
