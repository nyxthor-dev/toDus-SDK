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
    """Genera msg_id en formato hex de 32 chars, como usa ToDus oficial.

    Antes, se generaba como MD5 de un token aleatorio. ``secrets.token_hex(16)``
    es equivalente en longitud (32 hex chars) pero criptográficamente más
    directo y seguro.
    """
    return secrets.token_hex(16)


def normalize_phone(phone_number: str) -> str:
    """Normaliza número de teléfono al formato cubano (53XXXXXXXX, 10 dígitos).

    Acepta:
    - ``53XXXXXXXX`` (10 dígitos con prefijo internacional cubano)
    - ``XXXXXXXX`` (8 dígitos nacionales, sin prefijo; se le añade ``53``)

    Cualquier otra entrada (longitud incorrecta, prefijo de otro país, etc.)
    se rechaza con ``ValueError``.

    Nota: ToDus es una plataforma de mensajería cubana y los SMS solo se
    envían a números cubanos. No se aceptan números internacionales.
    """
    cleaned = re.sub(r"[\s+()\-.]", "", str(phone_number))
    if not cleaned.isdigit():
        raise ValueError(f"Número inválido: {phone_number}")
    national_len = 8
    country_code = "53"
    # Número nacional sin prefijo (8 dígitos)
    if len(cleaned) == national_len and not cleaned.startswith(country_code):
        return country_code + cleaned
    # Número completo con prefijo cubano (53 + 8 dígitos = 10 dígitos)
    if cleaned.startswith(country_code) and len(cleaned) == len(country_code) + national_len:
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
    """Escapa caracteres XML especiales.

    Escapa ``&``, ``<``, ``>``, apóstrofo (``'``) y comilla doble (``"``).
    Aunque todas las stanzas generadas por el SDK usan comillas simples, escapar
    también la comilla doble es defensivo: si en el futuro alguna stanza usa
    comillas dobles para un atributo, el contenido del usuario ya estará seguro.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
        .replace('"', "&quot;")
    )


def unescape_xml(text: str) -> str:
    """Revierte escape XML."""
    return (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&amp;", "&")
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
