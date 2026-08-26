"""Utilidades para ToDus."""

import hashlib
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


def generate_msg_id() -> str:
    """Genera msg_id en formato hex de 32 chars, como usa ToDus oficial."""
    return hashlib.md5(generate_token(16).encode()).hexdigest()


def normalize_phone(phone_number: str, country_code: str = "53") -> str:
    """Normaliza número de teléfono al formato internacional sin '+'.

    Por defecto asume Cuba (``53``): acepta ``53XXXXXXXX`` (10 dígitos)
    o el número nacional de 8 dígitos. Para otros países pasar
    ``country_code`` explícitamente (números E.164 de hasta 15 dígitos).

    A diferencia de versiones anteriores, rechaza entradas inválidas
    (longitudes incorrectas) en lugar de truncarlas silenciosamente.
    """
    cleaned = re.sub(r"[\s+()\-.]", "", str(phone_number))
    if not cleaned.isdigit():
        raise ValueError(f"Número inválido: {phone_number}")
    national_len = 8
    if cleaned.startswith(country_code) and len(cleaned) == len(country_code) + national_len:
        return cleaned
    if len(cleaned) == national_len:
        return country_code + cleaned
    if cleaned.startswith(country_code) and 11 <= len(cleaned) <= 15:
        # Número internacional E.164 válido con otro country code
        return cleaned
    raise ValueError(
        f"Número inválido: {phone_number} (se esperaban {national_len} dígitos "
        f"nacionales o {len(country_code) + national_len} con prefijo {country_code})"
    )


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

    # PNG: el chunk IHDR empieza en el offset 8 (longitud 4 + 'IHDR')
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        if len(data) >= 24 and data[12:16] == b'IHDR':
            width = int.from_bytes(data[16:20], 'big')
            height = int.from_bytes(data[20:24], 'big')

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
    """Genera un BlurHash simple basado en dimensiones.

    Genera un hash que varía según las dimensiones de la imagen.
    Para producción completa, usar la librería `blurhash-python`.
    """
    data = f"{width}x{height}".encode()
    digest = hashlib.md5(data).digest()
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[\\]^_{|}~"
    size_info = chars[40]  # 4x4 grid
    result = [size_info]
    for i in range(2, 7):
        val = digest[i % len(digest)]
        result.append(chars[val % len(chars)])
    return "".join(result)


def sanitize_filename(filename: str, file_type: int = 0) -> str:
    """Limpia caracteres problemáticos en el nombre del archivo para URLs, asegurando extensión según el tipo."""
    import os
    from .types import FileType

    # Mapeo de extensiones por defecto por tipo
    default_exts = {
        FileType.PICTURE: ".jpg",
        FileType.VIDEO: ".mp4",
        FileType.AUDIO: ".mp3",
        FileType.VOICE: ".opus",
        FileType.FILE: ".bin",
        FileType.PROFILE: ".jpg",
        FileType.PROFILE_THUMBNAIL: ".jpg",
    }

    default_ext = default_exts.get(file_type, ".bin")

    if not filename:
        # Generar nombre por defecto por tipo
        default_names = {
            FileType.PICTURE: "photo",
            FileType.VIDEO: "video",
            FileType.AUDIO: "audio",
            FileType.VOICE: "voice",
            FileType.FILE: "file",
            FileType.PROFILE: "profile",
            FileType.PROFILE_THUMBNAIL: "thumbnail",
        }
        stem = default_names.get(file_type, "file")
        ext = default_ext
    else:
        # Solo el nombre del archivo si es una ruta
        filename = os.path.basename(filename)

        # Separar nombre y extensión
        parts = filename.rsplit(".", 1)
        stem = parts[0]
        ext = "." + parts[1] if len(parts) > 1 else ""

        # Si no tiene extensión, usar la correspondiente al tipo
        if not ext:
            ext = default_ext

    # Reemplazar caracteres no permitidos en nombres de archivos o problemáticos en URLs
    stem_clean = re.sub(r'[\\/*?:"<>|\s]', "_", stem)

    # Limitar longitud para evitar URLs excesivamente largas
    if len(stem_clean) > 50:
        stem_clean = stem_clean[:47] + "..."

    return f"{stem_clean}{ext}"
