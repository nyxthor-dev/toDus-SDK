# Stanzas XML

El módulo `stanzas` contiene generadores de XML para todas las interacciones con el servidor XMPP de ToDus. Son usados internamente por los mixins, pero pueden usarse directamente para personalizaciones.

## Estructura

```
stanzas/
├── private.py    # Mensajes privados
├── group.py      # Mensajes de grupo
├── presence.py   # Presencia (online, offline, MUC)
├── utils.py      # IQ, ping, auth, MAM, upload
├── channels.py   # Canales
├── status.py     # Estados/Historias
├── privacy.py    # Privacidad
├── block.py      # Bloqueos
├── last.py       # Última conexión
├── location.py   # Ubicación
├── call.py       # Llamadas
└── profile.py    # @username
```

## Uso básico

Cada función retorna una cadena XML lista para enviar por el socket XMPP.

```python
from todus.stanzas import private, group, presence, utils

# Mensaje privado
xml = private.message("5351111111@im.todus.cu", "Hola")
sock.send(xml.encode())

# Mensaje de grupo
xml = group.group_message("grupo@muclight.im.todus.cu", "Hola grupo")

# Presencia
xml = presence.presence("Online", priority=5)
```

## Mensajes privados

| Función | Descripción |
|---------|-------------|
| `message(to, body, msg_id, msg_type, reply_to_id)` | Texto |
| `edit_message(to, new_body, original_msg_id, edit_id, reply_to_id)` | Edición |
| `file_message(to, url, file_type, caption, msg_id, ...)` | Archivo |
| `image_message(...)` | Imagen con metadatos |
| `image_message_simple(...)` | Imagen simple |
| `button_message(to, text, buttons, msg_id, reply_to_id)` | Botones |
| `contact_message(...)` | Contacto |
| `sticker_message(...)` | Sticker |
| `video_message(...)` | Video |
| `delete_message(...)` | Eliminación |
| `location_message(...)` | Ubicación |
| `event_message(...)` | Evento |

Estructura de un botón:

```python
button = {
    "text": "Enviar",
    "command": "cmd_type_send",
    "data": "Hola",
    "size": "0.82",        # FULL
    "color": "primary",    # opcional
    "row": True            # nueva fila
}
```

## Mensajes de grupo

Similar a `private.py` pero con `t='gc'` y destinados a JID de grupo. Incluye administración:

| Función | Descripción |
|---------|-------------|
| `group_update_name(to, name, msg_id)` | Cambiar nombre |
| `group_update_subject(to, subject, msg_id)` | Cambiar asunto |
| `group_update_avatar(to, avatar_url, msg_id)` | Cambiar avatar |
| `group_leave_iq(to, msg_id)` | Salir del grupo |
| `group_get_link_iq(to, msg_id)` | Obtener enlace |
| `group_set_link_iq(to, msg_id)` | Revocar enlace |
| `group_get_members_iq(to, msg_id)` | Lista miembros |
| `group_set_members_iq(to, affiliations, msg_id)` | Modificar roles |

## Utilidades XMPP

| Función | Descripción |
|---------|-------------|
| `iq(type_, iq_id, payload, to)` | IQ genérico |
| `build_iq(type_, to, query)` | IQ con ID autogenerado |
| `ping(ping_id)` | Ping XMPP |
| `chat_state(to, state, msg_id, msg_type)` | Estado de escritura |
| `receipt(to, msg_id, receipt_id, msg_type)` | ACK de entrega |
| `read_receipt(to, msg_id, receipt_id, msg_type)` | ACK de lectura |
| `ack(msg_id, to)` | TDACK |
| `keepalive()` | Espacio en blanco |
| `stream_open(host)` | Inicio de stream |
| `stream_restart(host)` | Reinicio de stream |
| `stream_close()` | Cierre de stream |
| `sasl_auth(authstr)` | Autenticación SASL PLAIN |
| `bind(iq_id)` | Resource bind |
| `mam_query(query_id, since, before, limit)` | Archivo de mensajes |
| `upload_query(iq_id, size, file_type, persistent, file_name)` | Reserva de subida |
| `download_query(iq_id, url)` | Resolución de descarga |

## Envío directo

Si necesitas control total, puedes enviar stanzas manualmente:

```python
with client._xmpp_session(client.token) as sock:
    sock.send(xml.encode())
```