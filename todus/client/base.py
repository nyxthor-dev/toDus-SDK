import logging
import re
import socket
import ssl
import string
from base64 import b64encode
from contextlib import contextmanager
import requests
import urllib3
from .. import constants, parser, stanza, util
from ..errors import ConnectionLostError, TokenExpiredError

logger = logging.getLogger("todus")


class ToDusClientBase:
    """Clase base para el cliente ToDus que maneja el socket XMPP y HTTP."""

    def __init__(
        self,
        version_name: str = constants.AUTH_VERSION_NAME,
        version_code: str = constants.AUTH_VERSION_CODE,
        proxy: str | None = None,
        verify_ssl: bool = False,
    ) -> None:
        self.version_name = version_name
        self.version_code = version_code
        self.proxy = proxy
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "gzip"})
        self.session.verify = verify_ssl

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }
        self._xml_parser = parser.IncrementalParser()

    def _parse_proxy(self, proxy_url: str):
        from urllib.parse import urlparse
        import socks

        parsed = urlparse(proxy_url)
        scheme = parsed.scheme.lower()

        if "socks5" in scheme:
            proxy_type = socks.SOCKS5
        elif "socks4" in scheme:
            proxy_type = socks.SOCKS4
        elif "http" in scheme:
            proxy_type = socks.HTTP
        else:
            raise ValueError(f"Tipo de proxy no soportado: {scheme}")

        port = parsed.port
        if port is None:
            if proxy_type == socks.HTTP:
                port = 8080
            else:
                port = 1080

        return proxy_type, parsed.hostname, port, parsed.username, parsed.password

    # --- XMPP Socket ---

    def _connect_xmpp(self) -> ssl.SSLSocket:
        if self.proxy:
            import socks
            proxy_type, host, port, username, password = self._parse_proxy(self.proxy)
            raw_sock = socks.socksocket(socket.AF_INET)
            raw_sock.set_proxy(proxy_type, host, port, username=username, password=password)
        else:
            raw_sock = socket.socket(socket.AF_INET)

        raw_sock.settimeout(constants.DEFAULT_TIMEOUT)
        raw_sock.connect((constants.XMPP_HOST, constants.XMPP_PORT))

        ctx = ssl.create_default_context()
        ctx.check_hostname = self.verify_ssl
        ctx.verify_mode = ssl.CERT_REQUIRED if self.verify_ssl else ssl.CERT_NONE
        sock = ctx.wrap_socket(raw_sock, server_hostname=constants.XMPP_HOST)
        sock.send(stanza.stream_open().encode())
        return sock

    def _recv_all(self, sock: ssl.SSLSocket) -> str | None:
        data = b""
        while True:
            try:
                chunk = sock.recv(constants.BUFFER_SIZE)
                if not chunk:
                    return None
                data += chunk
                if len(chunk) < constants.BUFFER_SIZE:
                    break
            except socket.timeout:
                break
            except OSError:
                return None
        return data.decode("utf-8", errors="replace")

    def _authstr_from_token(self, token: str) -> tuple[str, bytes]:
        payload = util.jwt_decode_payload(token)
        phone = payload.get("username", "")
        if not phone:
            match = re.search(r"(53\d{8})", token)
            if match:
                phone = match.group(1)
        authstr = b64encode((chr(0) + phone + chr(0) + token).encode("utf-8"))
        return phone, authstr

    def _process_handshake(self, response: str, sock, authstr: bytes, sid: str, state: dict) -> bool:
        phase = state.get("phase", "init")

        if phase == "init":
            if "<stream:features><es xmlns='x2'>" in response:
                sock.send(stanza.sasl_auth(authstr))
                state["phase"] = "auth_sent"
                return True
            if response.startswith("<?xml version='1.0'?><stream:stream"):
                if "<stream:features>" in response:
                    sock.send(stanza.sasl_auth(authstr))
                    state["phase"] = "auth_sent"
                return True
            return True

        if phase == "auth_sent":
            if "<ok xmlns='x2'/>" in response:
                sock.send(stanza.stream_restart().encode())
                state["phase"] = "restream"
                return True
            if "<not-authorized/>" in response:
                raise TokenExpiredError()
            return True

        if phase == "restream":
            if "<stream:features><b1 xmlns='x4'/>" in response:
                sock.send(stanza.bind(sid + "-1").encode())
                state["phase"] = "bind_sent"
                return True
            if response.startswith("<?xml version='1.0'?><stream:stream") and "<stream:features><b1 xmlns='x4'/>" in response:
                sock.send(stanza.bind(sid + "-1").encode())
                state["phase"] = "bind_sent"
                return True
            return True

        if phase == "bind_sent":
            if "t='result' i='" + sid + "-1'>" in response:
                return False
            if "<not-authorized/>" in response:
                raise TokenExpiredError()
            return True

        return True

    def _handshake(self, sock: ssl.SSLSocket, token: str) -> None:
        _, authstr = self._authstr_from_token(token)
        sid = util.generate_token(5)
        state = {"phase": "init"}

        while True:
            response = self._recv_all(sock)
            if response is None:
                raise ConnectionLostError("Servidor cerro conexion durante handshake")
            if response == "":
                continue

            if not self._process_handshake(response, sock, authstr, sid, state):
                return

    # --- Context Manager XMPP ---

    @contextmanager
    def _xmpp_session(self, token: str):
        sock = self._connect_xmpp()
        try:
            self._handshake(sock, token)
            sock.send(stanza.presence().encode())
            yield sock
        finally:
            try:
                sock.send(stanza.stream_close().encode())
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass