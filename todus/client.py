"""Cliente XMPP/HTTP para ToDus."""

import json
import logging
import os
import re
import socket
import ssl
import string
import threading
import time
from base64 import b64decode, b64encode
from contextlib import contextmanager
from typing import Callable

import requests

from . import constants, parser, stanza, util
from .errors import (
    AuthenticationError,
    ConnectionLostError,
    TokenExpiredError,
    UploadError,
)
from .types import FileType

logger = logging.getLogger("todus")


class ToDusClient:
    """Cliente stateless para la API de ToDus."""

    def __init__(
        self,
        version_name: str = constants.AUTH_VERSION_NAME,
        version_code: str = constants.AUTH_VERSION_CODE,
    ) -> None:
        self.version_name = version_name
        self.version_code = version_code
        self.session = requests.Session()
        self.session.headers.update({"Accept-Encoding": "gzip"})
        self._xml_parser = parser.IncrementalParser()

    # --- Auth HTTP ---

    def request_code(self, phone_number: str) -> None:
        headers = {
            "Host": "auth.todus.cu",
            "User-Agent": "ToDus " + self.version_name + " Auth",
            "Content-Type": "application/x-protobuf",
        }
        data = (
            bytes([0x0A, 0x0A])
            + phone_number.encode()
            + bytes([0x12, 0x96, 0x01])
            + util.generate_token(150).encode()
        )
        resp = self.session.post(
            "https://auth.todus.cu/v2/auth/users.reserve",
            data=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()

    def validate_code(self, phone_number: str, code: str) -> str:
        headers = {
            "Host": "auth.todus.cu",
            "User-Agent": "ToDus " + self.version_name + " Auth",
            "Content-Type": "application/x-protobuf",
        }
        data = (
            bytes([0x0A, 0x0A])
            + phone_number.encode()
            + bytes([0x12, 0x96, 0x01])
            + util.generate_token(150).encode()
            + bytes([0x1A, 0x06])
            + code.encode()
        )
        resp = self.session.post(
            "https://auth.todus.cu/v2/auth/users.register",
            data=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.content
        try:
            if b"`" in content:
                idx = content.index(b"`") + 1
                return content[idx : idx + 96].decode("utf-8")
            return content[5:166].decode("utf-8")
        except UnicodeDecodeError:
            raw = content.decode("latin-1", errors="ignore")
            match = re.search(r"[a-f0-9]{96}", raw)
            if match:
                return match.group(0)
            return "".join(c for c in raw if c in string.printable and c not in "\r\n")[:96]

    def login(self, phone_number: str, password: str) -> str:
        headers = {
            "Host": "auth.todus.cu",
            "user-agent": "ToDus " + self.version_name + " Auth",
            "content-type": "application/x-protobuf",
        }
        data = (
            bytes([0x0A, 0x0A])
            + phone_number.encode()
            + bytes([0x12, 0x96, 0x01])
            + util.generate_token(150).encode()
            + bytes([0x12, 0x60])
            + password.encode()
            + bytes([0x1A, 0x05])
            + self.version_code.encode()
        )
        resp = self.session.post(
            "https://auth.todus.cu/v2/auth/token",
            data=data,
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 403:
            raise AuthenticationError("Credenciales invalidas")
        resp.raise_for_status()
        return "".join([c for c in resp.text if c in string.printable])

    # --- XMPP Socket ---

    def _connect_xmpp(self) -> ssl.SSLSocket:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        sock = ctx.wrap_socket(socket.socket(socket.AF_INET))
        sock.settimeout(constants.DEFAULT_TIMEOUT)
        sock.connect((constants.XMPP_HOST, constants.XMPP_PORT))
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
        phone, authstr = self._authstr_from_token(token)
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

    # --- Mensajeria ---

    def send_message(self, token: str, to_jid: str, body: str) -> None:
        msg = stanza.message(to_jid, body)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())

    def send_file_message(self, token: str, to_jid: str, url: str, file_type: FileType, caption: str = "", file_name: str = "", file_size: int = 0) -> None:
        msg = stanza.file_message(to_jid, url, int(file_type), caption, file_name=file_name, file_size=file_size)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())

    def send_chat_state(self, token: str, to_jid: str, state: str) -> None:
        st = stanza.chat_state(to_jid, state)
        with self._xmpp_session(token) as sock:
            sock.send(st.encode())

    def listen_messages(self, token: str, callback: Callable[[dict], None]) -> None:
        while True:
            try:
                with self._xmpp_session(token) as sock:
                    self._listen_loop(sock, callback)
            except TokenExpiredError:
                raise
            except (ConnectionLostError, OSError, socket.error):
                time.sleep(15)

    def _listen_loop(self, sock: ssl.SSLSocket, callback: Callable[[dict], None]) -> None:
        stop_event = threading.Event()
        ping_id = util.generate_token(5)
        ka = threading.Thread(
            target=self._keepalive_worker,
            args=(sock, stop_event, ping_id),
            daemon=True,
        )
        ka.start()
        self._xml_parser.reset()

        try:
            while True:
                try:
                    response = self._recv_all(sock)
                except OSError as e:
                    raise ConnectionLostError(e)

                if response is None:
                    raise ConnectionLostError("Servidor cerro conexion")

                if response == "":
                    continue

                stanzas = self._xml_parser.feed(response)

                for msg in stanzas:
                    if msg.get("deleted"):
                        continue
                    if msg.get("body") or msg.get("url"):
                        msg_id = msg.get("id", "")
                        msg_from = msg.get("from", "")
                        if msg_id and msg_from:
                            try:
                                receipt = stanza.receipt(msg_from, msg_id)
                                sock.send(receipt.encode())
                            except Exception:
                                pass
                        callback(msg)

        finally:
            stop_event.set()
            self._xml_parser.reset()

    def _keepalive_worker(self, sock: ssl.SSLSocket, stop: threading.Event, ping_id: str) -> None:
        while not stop.is_set():
            time.sleep(constants.KEEPALIVE_INTERVAL)
            if stop.is_set():
                break
            try:
                sock.send(stanza.ping(ping_id).encode())
            except OSError:
                break

    # --- Archivos ---

    def reserve_upload_url(self, token: str, size: int, file_type: FileType) -> tuple[str, str]:
        phone, authstr = self._authstr_from_token(token)
        sid = util.generate_token(5)
        up_url = down_url = ""

        with self._xmpp_session(token) as sock:
            sock.send(stanza.upload_query(sid, size, int(file_type)).encode())
            while True:
                response = self._recv_all(sock)
                if response is None:
                    raise ConnectionLostError()
                if response == "":
                    continue
                if "i='" + sid + "-3'" in response and "put='" in response:
                    match = re.match(r".*put='(.*)' get='(.*)' stat.*", response)
                    if match:
                        up_url = match.group(1).replace("amp;", "")
                        down_url = match.group(2)
                    break
                if "<not-authorized/>" in response:
                    raise TokenExpiredError()

        return up_url, down_url

    def get_real_download_url(self, token: str, url: str) -> str:
        phone, authstr = self._authstr_from_token(token)
        sid = util.generate_token(5)

        with self._xmpp_session(token) as sock:
            sock.send(stanza.download_query(sid, url).encode())
            while True:
                response = self._recv_all(sock)
                if response is None:
                    raise ConnectionLostError()
                if response == "":
                    continue
                if "i='" + sid + "-2'" in response and "du='" in response:
                    match = re.match(".*du='(.*)' stat.*", response)
                    if match:
                        return match.group(1).replace("amp;", "")
                    break
                if "<not-authorized/>" in response:
                    raise TokenExpiredError()

        return ""

    def upload_file(self, token: str, data: bytes, file_type: FileType = FileType.FILE) -> str:
        up_url, down_url = self.reserve_upload_url(token, len(data), file_type)
        resp = requests.put(
            up_url,
            data=data,
            headers={"Content-Length": str(len(data))},
            timeout=60,
        )
        resp.raise_for_status()
        return down_url

    def download_file(self, token: str, url: str, path: str) -> int:
        real_url = self.get_real_download_url(token, url)
        headers = {
            "User-Agent": "ToDus " + self.version_name + " HTTP-Download",
            "Authorization": "Bearer " + token,
        }
        temp_path = path + ".part"
        size = -1
        with open(temp_path, "ab") as f:
            pos = f.tell()
            while pos < size or size == -1:
                if pos:
                    headers["Range"] = "bytes=" + str(pos) + "-"
                try:
                    with self.session.get(real_url, headers=headers, stream=True, timeout=60) as resp:
                        resp.raise_for_status()
                        size = pos + int(resp.headers.get("Content-Length", 0))
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                except Exception:
                    time.sleep(5)
                pos = f.tell()
        os.rename(temp_path, path)
        return size

    def download_file_to_folder(self, token: str, url: str, folder: str, filename: str = "") -> tuple[int, str]:
        print("   [DEBUG] Iniciando descarga...")
        print("   [DEBUG] URL original: " + url[:80] + "...")
        print("   [DEBUG] Token presente: " + str(bool(token)))

        headers = {
            "User-Agent": "ToDus " + self.version_name + " HTTP-Download",
            "Authorization": "Bearer " + token,
        }

        os.makedirs(folder, exist_ok=True)

        if not filename:
            filename = os.path.basename(url.split("?")[0]) or "download"

        final_path = os.path.join(folder, filename)
        temp_path = final_path + ".part"

        print("   [DEBUG] Guardando en: " + temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("   [DEBUG] Borrado .part anterior")

        print("   [DEBUG] Intentando descarga directa...")
        try:
            print("   [DEBUG] HEAD request a URL...")
            test_resp = self.session.head(url, headers=headers, timeout=15, allow_redirects=True)
            print("   [DEBUG] HEAD status: " + str(test_resp.status_code))
            print("   [DEBUG] HEAD headers: " + str(dict(test_resp.headers)))

            if test_resp.status_code in (200, 206, 401, 403, 302, 301):
                print("   [DEBUG] URL directa parece valida, procediendo con GET")
                real_url = url
            else:
                print("   [DEBUG] HEAD fallo, intentando resolver via XMPP...")
                real_url = self.get_real_download_url(token, url)
                print("   [DEBUG] URL resuelta via XMPP: " + (real_url[:80] if real_url else "VACIA") + "...")
                if not real_url:
                    raise Exception("No se pudo resolver URL de descarga")
        except Exception as e:
            print("   [DEBUG] Error en HEAD: " + str(e))
            print("   [DEBUG] Intentando resolver via XMPP...")
            try:
                real_url = self.get_real_download_url(token, url)
                print("   [DEBUG] URL resuelta: " + (real_url[:80] if real_url else "VACIA") + "...")
                if not real_url:
                    raise Exception("No se pudo resolver URL")
            except Exception as e2:
                print("   [DEBUG] Error XMPP tambien: " + str(e2))
                raise Exception("No se pudo obtener URL de descarga: " + str(e2))

        print("   [DEBUG] Iniciando GET a: " + real_url[:80] + "...")
        size = -1
        downloaded = 0
        start_time = time.time()
        last_progress = 0

        with open(temp_path, "wb") as f:
            try:
                with self.session.get(real_url, headers=headers, stream=True, timeout=300) as resp:
                    print("   [DEBUG] GET status: " + str(resp.status_code))
                    print("   [DEBUG] GET headers: Content-Length=" + str(resp.headers.get("Content-Length", "N/A")))

                    if resp.status_code not in (200, 206):
                        raise Exception("HTTP " + str(resp.status_code) + ": " + resp.text[:100])

                    size = int(resp.headers.get("Content-Length", 0))
                    print("   [DEBUG] Tamano total: " + util.format_size(size))

                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if downloaded - last_progress >= (500 * 1024):
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                print("   Descargando " + util.format_size(downloaded) + " / " + util.format_size(size) + " @ " + util.format_size(int(speed)) + "/s")
                                last_progress = downloaded

                    print("   [DEBUG] Descarga completada: " + str(downloaded) + " bytes")
            except Exception as e:
                print("   [DEBUG] Error durante GET: " + str(e))
                raise

        print("   [DEBUG] Renombrando " + temp_path + " -> " + final_path)
        os.rename(temp_path, final_path)
        print("   Descarga completa: " + util.format_size(downloaded))
        return downloaded, final_path

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


class ToDusClient2(ToDusClient):
    """Cliente stateful con auto-login y auto-reconnect."""

    def __init__(self, phone_number: str, password: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.password = password
        self._token = ""

    def _authstr_from_token(self, token: str) -> tuple[str, bytes]:
        phone, authstr = super()._authstr_from_token(token)
        if not phone and self.phone_number:
            phone = util.normalize_phone(self.phone_number)
            authstr = b64encode((chr(0) + phone + chr(0) + token).encode("utf-8"))
        return phone, authstr

    @property
    def token(self) -> str:
        return self._token

    @property
    def registered(self) -> bool:
        return bool(self.phone_number and self.password)

    @property
    def logged(self) -> bool:
        return bool(self._token)

    def login(self) -> None:
        if not self.password:
            raise AuthenticationError("No hay password")
        self._token = super().login(self.phone_number, self.password)

    def request_code(self) -> None:
        super().request_code(self.phone_number)

    def validate_code(self, code: str) -> None:
        self.password = super().validate_code(self.phone_number, code)

    def send_message(self, to_phone: str, body: str) -> None:
        if not self._token:
            raise AuthenticationError("No autenticado")
        to_jid = util.build_jid(to_phone)
        super().send_message(self._token, to_jid, body)

    def send_file_message(self, to_phone: str, url: str, file_type: FileType, caption: str = "", file_name: str = "", file_size: int = 0) -> None:
        if not self._token:
            raise AuthenticationError("No autenticado")
        to_jid = util.build_jid(to_phone)
        super().send_file_message(self._token, to_jid, url, file_type, caption, file_name=file_name, file_size=file_size)

    def send_chat_state(self, to_phone: str, state: str) -> None:
        if not self._token:
            raise AuthenticationError("No autenticado")
        super().send_chat_state(self._token, util.build_jid(to_phone), state)

    def listen_messages(self, callback: Callable[[dict], None]) -> None:
        if not self._token:
            raise AuthenticationError("No autenticado")
        while True:
            try:
                super().listen_messages(self._token, callback)
            except TokenExpiredError:
                self.login()
            except (ConnectionLostError, OSError, socket.error):
                time.sleep(15)

    # --- API homogeneizada: todos los metodos usan self._token ---

    def reserve_upload_url(self, size: int, file_type: FileType) -> tuple[str, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().reserve_upload_url(self._token, size, file_type)

    def get_real_download_url(self, url: str) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().get_real_download_url(self._token, url)

    def upload_file(self, data: bytes, file_type: FileType = FileType.FILE) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        up_url, down_url = self.reserve_upload_url(len(data), file_type)
        resp = requests.put(
            up_url,
            data=data,
            headers={"Content-Length": str(len(data))},
            timeout=60,
        )
        resp.raise_for_status()
        return down_url

    def download_file(self, url: str, path: str) -> int:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().download_file(self._token, url, path)

    def download_file_to_folder(self, url: str, folder: str, filename: str = "") -> tuple[int, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().download_file_to_folder(self._token, url, folder, filename)
