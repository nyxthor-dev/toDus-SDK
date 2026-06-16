"""Utilidades para ToDus."""

import json
import re
import secrets
import string
from base64 import b64decode
from datetime import datetime


def generate_token(length: int = 8) -> str:
    """Genera un token alfanumérico aleatorio criptográficamente seguro."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def normalize_phone(phone_number: str) -> str:
    """Normaliza número cubano a formato 53XXXXXXXX."""
    phone_number = "".join(phone_number.lstrip("+").split())
    match = re.match(r"(53)?(\d{8})", phone_number)
    if not match:
        raise ValueError(f"Número inválido: {phone_number}")
    return "53" + match.group(2)


def build_jid(phone_number: str) -> str:
    """Construye JID ToDus desde número de teléfono."""
    return normalize_phone(phone_number) + "@im.todus.cu"


def parse_jid(jid: str) -> tuple[str, str]:
    """Extrae (phone, resource) de un JID."""
    parts = jid.split("/", 1)
    phone = parts[0].split("@")[0]
    resource = parts[1] if len(parts) > 1 else ""
    return phone, resource


def escape_xml(text: str) -> str:
    """Escapa caracteres XML especiales, incluyendo apóstrofos."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
    )


def unescape_xml(text: str) -> str:
    """Revierte escape XML."""
    return (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&apos;", "'")
    )


def jwt_decode_payload(token: str) -> dict:
    """Decodifica payload de JWT sin verificar firma."""
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding
    try:
        decoded = b64decode(payload).decode("utf-8", errors="ignore")
        return json.loads(decoded)
    except Exception:
        return {}


def timestamp_ms() -> int:
    """Timestamp actual en milisegundos."""
    return int(datetime.now().timestamp() * 1000)


def format_size(size_bytes: int) -> str:
    """Formatea tamaño en bytes a human readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_image_dimensions(data: bytes) -> tuple[int, int]:
    """Extrae dimensiones de imagen JPEG/PNG sin decodificar completamente."""
    width = height = 0

    # PNG
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        for i in range(0, len(data) - 8, 8):
            if data[i:i+4] == b'IHDR':
                width = int.from_bytes(data[i+4:i+8], 'big')
                height = int.from_bytes(data[i+8:i+12], 'big')
                break

    # JPEG
    elif data.startswith(b'\xff\xd8'):
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xff:
                i += 1
                continue
            marker = data[i+1]
            if marker == 0xc0 or marker == 0xc2:
                height = int.from_bytes(data[i+5:i+7], 'big')
                width = int.from_bytes(data[i+7:i+9], 'big')
                break
            i += 2 + int.from_bytes(data[i+2:i+4], 'big')

    return width, height


def generate_blurhash(width: int, height: int) -> str:
    """Genera un BlurHash simple basado en dimensiones."""
    # Por ahora devolvemos un hash genérico
    # En producción usar librería blurhash
    return "LFE_@w00ay00ay00ay00ay00ay00ay"
