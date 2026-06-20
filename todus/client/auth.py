import string
import re
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
        resp = self.session.post(
            "https://auth.todus.cu/v2/auth/users.reserve",
            data=data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()

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
            + bytes([0x12, 0x96, 0x01])
            + util.generate_token(150).encode()
            + bytes([0x12, len(password_bytes)])
            + password_bytes
            + bytes([0x1A, len(version_bytes)])
            + version_bytes
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
