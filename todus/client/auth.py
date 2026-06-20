import string
import re
import requests
from ..errors import AuthenticationError
from .. import util


class ToDusAuthMixin:
    """Mixin que contiene los métodos de autenticación HTTP de ToDus."""

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
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/users.reserve",
                data=data,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Error al solicitar código: {e}") from e

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
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/users.register",
                data=data,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Error al validar código: {e}") from e

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
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/token",
                data=data,
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 403:
                raise AuthenticationError("Credenciales inválidas")
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Error de login: {e}") from e
        return "".join([c for c in resp.text if c in string.printable])