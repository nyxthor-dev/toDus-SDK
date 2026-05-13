"""Utilidades para ToDus."""

import json
import random
import re
import string
from base64 import b64decode
from datetime import datetime


def generate_token(length: int = 8) -> str:
    """Genera un token alfanumérico aleatorio."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


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
    """Escapa caracteres XML especiales."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def unescape_xml(text: str) -> str:
    """Revierte escape XML."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


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
