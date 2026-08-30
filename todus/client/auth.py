import string
import re
import requests
from ..errors import AuthenticationError
from .. import util


class ToDusAuthMixin:
    """Mixin que contiene los métodos de autenticación HTTP de ToDus."""

    def request_code(self, phone_number: str) -> None:
        phone = util.normalize_phone(phone_number)
        headers = {
            "Host": "auth.todus.cu",
            "User-Agent": "ToDus " + self.version_name + " Auth",
            "Content-Type": "application/x-protobuf",
        }
        data = (
            bytes([0x0A, 0x0A])
            + phone.encode()
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
            if resp.status_code in (401, 403):
                raise AuthenticationError(
                    f"Auth error solicitando código (HTTP {resp.status_code})"
                )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Error de red solicitando código: {e}") from e

    def validate_code(self, phone_number: str, code: str) -> str:
        phone = util.normalize_phone(phone_number)
        code = code.strip()
        headers = {
            "Host": "auth.todus.cu",
            "User-Agent": "ToDus " + self.version_name + " Auth",
            "Content-Type": "application/x-protobuf",
        }
        code_bytes = code.encode()
        data = (
            bytes([0x0A, 0x0A])
            + phone.encode()
            + bytes([0x12, 0x96, 0x01])
            + util.generate_token(150).encode()
            + bytes([0x1A, len(code_bytes)])
            + code_bytes
        )
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/users.register",
                data=data,
                headers=headers,
                timeout=30,
            )
            if resp.status_code in (401, 403):
                raise AuthenticationError(
                    f"Código de verificación inválido (HTTP {resp.status_code})"
                )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Error de red validando código: {e}") from e
        content = resp.content
        try:
            if b"`" in content:
                idx = content.index(b"`") + 1
                return content[idx: idx + 96].decode("utf-8")
            return content[5:166].decode("utf-8")
        except UnicodeDecodeError:
            raw = content.decode("latin-1", errors="ignore")
            match = re.search(r"[a-f0-9]{96}", raw)
            if match:
                return match.group(0)
            return "".join(c for c in raw if c in string.printable and c not in "\r\n")[:96]

    def login(self, phone_number: str, password: str) -> str:
        phone = util.normalize_phone(phone_number)
        password = password.strip()
        headers = {
            "Host": "auth.todus.cu",
            "user-agent": "ToDus " + self.version_name + " Auth",
            "content-type": "application/x-protobuf",
        }
        password_bytes = password.encode()
        version_bytes = self.version_code.encode()
        data = (
            bytes([0x0A, 0x0A])
            + phone.encode()
            + bytes([0x12, len(password_bytes)])
            + password_bytes
            + bytes([0x1A, 0x96, 0x01])
            + util.generate_token(150).encode()
            + bytes([0x22, len(version_bytes)])
            + version_bytes
        )
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/token",
                data=data,
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as e:
            raise AuthenticationError(f"Error de red en login: {e}") from e
        if resp.status_code == 403:
            raise AuthenticationError("Credenciales invalidas")
        if resp.status_code == 401:
            raise AuthenticationError("No autorizado")
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Login falló (HTTP {resp.status_code}): {e}") from e
        # Limpiar token: solo caracteres alfanuméricos y puntos válidos para JWT
        raw = resp.text.strip()
        token_clean = "".join(
            c for c in raw
            if c in string.ascii_letters + string.digits + "._-"
        )
        if not token_clean or "." not in token_clean:
            raise AuthenticationError("Token inválido recibido del servidor")
        return token_clean
