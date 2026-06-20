"""Utilidades para ToDus."""

import json
import re
import secrets
import string
from base64 import b64decode
from datetime import datetime
from typing import Tuple, Optional, Literal

# Constantes XMPP
XMPP_HOST = "im.todus.cu"
MUCLIGHT_HOST = "muclight.im.todus.cu"


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
    return normalize_phone(phone_number) + "@" + XMPP_HOST


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


# ================================================================
#  NUEVAS FUNCIONES PARA RESOLUCIÓN AUTOMÁTICA DE JIDs
# ================================================================

def is_phone_number(text: str) -> bool:
    """Detecta si el texto es un número de teléfono cubano (10 dígitos empezando por 53)."""
    if not text:
        return False
    cleaned = re.sub(r'[\s\+\(\)-]', '', text)
    return bool(re.match(r'^53\d{8}$', cleaned))


def is_full_jid(text: str) -> bool:
    """Detecta si el texto es un JID completo (contiene @ y un dominio conocido)."""
    if not text:
        return False
    return bool(re.search(r'@(im\.todus\.cu|muclight\.im\.todus\.cu)', text))


def is_group_id(text: str) -> bool:
    """Detecta si el texto parece un ID de grupo (no es número, no tiene @)."""
    if not text:
        return False
    # Si es número de teléfono, no es grupo
    if is_phone_number(text):
        return False
    # Si tiene @, ya lo manejamos en is_full_jid
    if '@' in text:
        return False
    return True


def parse_jid_parts(jid: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parsea un JID completo y devuelve (local, domain, resource).
    Ejemplo: "usuario@im.todus.cu/resource" → ("usuario", "im.todus.cu", "resource")
    """
    resource = None
    if '/' in jid:
        jid, resource = jid.split('/', 1)
    
    if '@' not in jid:
        return jid, None, resource
    
    local, domain = jid.split('@', 1)
    return local, domain, resource


def resolve_target(target: str) -> dict:
    """
    Resuelve automáticamente cualquier formato de destino.
    Devuelve un dict con:
        - type: 'private' o 'group' o 'unknown'
        - jid: JID completo para usar en la stanza
        - phone: número de teléfono (si es privado)
        - group_id: ID del grupo (si es grupo)
        - resource: recurso (si se especificó)
        - raw: entrada original
    """
    if not target:
        return {
            'type': 'unknown',
            'jid': '',
            'phone': None,
            'group_id': None,
            'resource': None,
            'raw': target,
        }
    
    raw = target.strip()
    
    # 1. Si es JID completo
    if is_full_jid(raw):
        local, domain, resource = parse_jid_parts(raw)
        if domain == MUCLIGHT_HOST:
            return {
                'type': 'group',
                'jid': raw,
                'group_id': local,
                'resource': resource,
                'phone': None,
                'raw': raw,
            }
        elif domain == XMPP_HOST:
            return {
                'type': 'private',
                'jid': raw,
                'phone': local,
                'resource': resource,
                'group_id': None,
                'raw': raw,
            }
    
    # 2. Si es número de teléfono (con o sin +, con espacios, guiones)
    if is_phone_number(raw):
        phone = normalize_phone(raw)
        jid = f"{phone}@{XMPP_HOST}"
        return {
            'type': 'private',
            'jid': jid,
            'phone': phone,
            'resource': None,
            'group_id': None,
            'raw': raw,
        }
    
    # 3. Si es ID de grupo (sin @)
    if is_group_id(raw):
        jid = f"{raw}@{MUCLIGHT_HOST}"
        return {
            'type': 'group',
            'jid': jid,
            'group_id': raw,
            'resource': None,
            'phone': None,
            'raw': raw,
        }
    
    # 4. Si no se pudo resolver, devolver como está (fallback)
    return {
        'type': 'unknown',
        'jid': raw,
        'phone': None,
        'group_id': None,
        'resource': None,
        'raw': raw,
    }


# Cache para nombres de contacto (opcional)
_contact_cache = {}


def cache_contact(phone: str, name: str) -> None:
    """Guarda un nombre de contacto en caché."""
    if phone and name:
        _contact_cache[phone] = name


def get_cached_contact(phone: str) -> Optional[str]:
    """Obtiene un nombre de contacto de la caché."""
    return _contact_cache.get(phone)


def clear_contact_cache() -> None:
    """Limpia la caché de contactos."""
    _contact_cache.clear()