# Grupos MUC Light

El SDK soporta grupos MUC Light a través de la propiedad `groups` del cliente.

## Acceso

```python
client = ToDusClient2("5312345678", "password")
client.login()

groups = client.groups
```

## Unirse y salir

```python
groups.join(group_id, nickname="MiApodo")
groups.leave(group_id)
```

## Envío de mensajes

### Texto

```python
groups.send_message(group_id, "Hola a todos", reply_to_id="")
```

### Imagen

```python
groups.send_image(
    group_id, url="https://...", file_name="foto.jpg",
    file_size=12345, width=800, height=600,
    thumbnail="...", caption="Mi foto", reply_to_id=""
)
```

### Video

```python
groups.send_video(
    group_id, url="https://...", video_id="vid123",
    file_name="video.mp4", file_size=12345, duration=60,
    width=1280, height=720, thumbnail="...", caption="Mi video"
)
```

### Sticker, contacto, ubicación y evento

```python
groups.send_sticker(group_id, sticker_id="stk1", sticker_name="feliz",
                     sticker_pack="pack1", sticker_hash="abc123")

groups.send_contact(group_id, contact_id="c1", contact_name="Juan",
                      contact_phone="5351234567")

groups.send_location(group_id, lat=23.1136, lon=-82.3666,
                       zoom=11.0, text="Mi ubicación")

import time
groups.send_event(group_id, title="Reunión", start=int(time.time()),
                    end=int(time.time()) + 3600, all_day=False,
                    ics_data="BEGIN:VCALENDAR...", event_id="ev1")
```

## Administración

```python
# Nombre y descripción
groups.set_name(group_id, "Nuevo Nombre")
groups.set_subject(group_id, "Descripción del grupo")

# Avatar
groups.set_avatar(group_id, "https://.../avatar.jpg", "https://.../thumb.jpg")

# Invitación
msg_id = groups.get_invite_link(group_id)
groups.revoke_invite_link(group_id)

# Miembros
msg_id = groups.get_members(group_id)
# members = groups.parse_members_response(msg["raw"])

# Roles
from todus import GroupRole
groups.set_member_role(group_id, "5351111111", GroupRole.MODERATOR)

# Expulsar
groups.kick_member(group_id, "5351111111")
```

## Editar y eliminar mensajes

```python
groups.edit_message(group_id, new_body="Texto corregido",
                    original_msg_id="id_original")

groups.delete_message(group_id, message_id="id_a_eliminar")
```

## Eventos de grupo

El parser detecta automáticamente eventos de miembros:

```python
def on_message(msg):
    if msg.get("is_group_event"):
        event = msg.get("event")
        print(f"Evento de grupo: {event}")

client.listen_messages(on_message)
```

**Eventos disponibles:**

- `MEMBER_JOINED` — alguien se unió
- `MEMBER_LEFT` — alguien salió
- `MEMBER_KICKED` — alguien fue expulsado
- `MEMBER_BANNED` — alguien fue baneado
- `SUBJECT_CHANGED` — el nombre cambió
- `ROOM_CREATED` — grupo creado
- `ROOM_DESTROYED` — grupo eliminado
