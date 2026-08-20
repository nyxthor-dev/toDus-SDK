# Utilidades

Funciones auxiliares en `todus.util`.

## Normalización

| Función | Descripción | Ejemplo |

|---------|-------------|--------|
| `normalize_phone(phone) -> str` | Normaliza número cubano a `53XXXXXXXX` | `normalize_phone("+5351234567")` → `"5351234567"` |
| `build_jid(phone) -> str` | Construye JID ToDus | `build_jid("5312345678")` → `"5312345678@im.todus.cu"` |
| `parse_jid(jid) -> tuple` | Extrae teléfono y resource | `parse_jid("5312345678@im.todus.cu/res")` → `("5312345678", "res")` |

## Tokens y JWT

| Función | Descripción |
|---------|-------------|
| `generate_token(length=8) -> str` | Token alfanumérico seguro (usando `secrets`) |
| `jwt_decode_payload(token) -> dict` | Decodifica payload JWT sin verificar firma |

## XML

| Función | Descripción |
|---------|-------------|
| `escape_xml(text) -> str` | Escapa `&`, `<`, `>`, `'` |
| `unescape_xml(text) -> str` | Revierte escape XML |

## Archivos

| Función | Descripción |
|---------|-------------|
| `format_size(bytes) -> str` | Formatea a B, KB, MB, GB |
| `get_image_dimensions(data) -> tuple` | Extrae dimensiones de JPEG/PNG sin decodificar |
| `sanitize_filename(name, file_type) -> str` | Limpia nombre y añade extensión |
| `generate_blurhash(width, height) -> str` | BlurHash genérico por dimensiones |

## Tiempo

| Función | Descripción |
|---------|-------------|
| `timestamp_ms() -> int` | Timestamp actual en milisegundos |