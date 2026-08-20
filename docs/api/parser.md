# Parser

Parsea las stanzas XML entrantes del socket XMPP, manejando fragmentación TCP.

## parse_todus_message(stanza) -> dict

Parsea una stanza `<m>` de ToDus.

```python
from todus.parser import parse_todus_message

parsed = parse_todus_message(raw_xml)
print(parsed["body"])  # "Hola"
```

**Campos principales:**

| Campo | Descripción |
|-------|-------------|
| `from`, `to`, `id`, `type` | Metadatos XMPP |
| `body` | Texto del mensaje |
| `is_group` | `True` si es mensaje de grupo |
| `group_id`, `sender_phone` | Disponibles en mensajes de grupo |
| `reply_to` | ID del mensaje respondido |
| `url`, `file_name`, `file_size`, `file_id` | Archivos |
| `image_width`, `image_height`, `image_thumbnail` | Imágenes |
| `video_url`, `video_duration`, `video_width`, `video_height` | Videos |
| `sticker_id`, `sticker_name`, `sticker_pack` | Stickers |
| `contact_id`, `contact_name`, `contact_phone` | Contactos |
| `location_lat`, `location_lon`, `location_zoom` | Ubicación |
| `buttons` | Lista de diccionarios con `text`, `command`, `data` |
| `receipt`, `receipt_type` | Confirmaciones (`delivered` / `read`) |
| `chat_state` | `composing` o `paused` |
| `deleted` | ID de mensaje eliminado |
| `raw` | Stanza XML original |

## parse_presence(stanza) -> dict

```python
{"from": "...", "status": "Online", "show": "chat", "priority": 5}
```

## parse_iq(stanza) -> dict

```python
{"from": "...", "type": "result", "upload_url": "...", "download_url": "..."}
```

Campos especiales según el tipo de IQ: `upload_url`, `download_url`, `real_url`, `error`, `query`.

## parse_tdack(stanza) -> dict

```python
{"type": "tdack", "message_id": "..."}
```

## IncrementalParser

Parser que maneja stanzas fragmentadas en múltiples paquetes TCP. Usado internamente por `ToDusClientBase` en `_listen_loop`.

```python
parser = IncrementalParser()
stanzas = parser.feed(recv_data)
for stanza in stanzas:
    # Procesar cada stanza completa
```

| Método | Descripción |
|--------|-------------|
| `feed(chunk) -> list[dict]` | Alimenta con nuevo chunk, retorna stanzas completas |
| `reset()` | Limpia el buffer interno |