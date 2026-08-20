# Inicio Rápido

Escenarios más comunes usando el SDK.

## Cliente básico

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="tu_contraseña")
client.login()
client.send_message("5387654321", "Hola, ¿cómo estás?")
```

## Cliente con cola persistente

Ideal para bots que necesitan garantizar la entrega de mensajes.

```python
from todus import ToDusClientWithQueue

client = ToDusClientWithQueue(
    phone_number="5312345678",
    password="tu_contraseña",
    enable_queue=True,
    queue_db_path="~/.todus/messages.db"
)
client.login()

msg_id = client.send_message_queued("5387654321", "Mensaje con garantía")
```

## Escuchar mensajes

```python
def handle_message(msg):
    if msg.get("is_group"):
        return
    sender = msg.get("from", "")
    body = msg.get("body", "")
    print(f"{sender}: {body}")

client.listen_messages(handle_message)
```

!!! tip "Multitarea"

    Si necesitas hacer otras cosas mientras escuchas, ejecuta `listen_messages` en un hilo separado:

    ```python
    import threading
    threading.Thread(
        target=client.listen_messages,
        args=(handle_message,),
        daemon=True
    ).start()
    ```

## Trabajar con archivos

### Subir y enviar imagen

```python
from todus.types import FileType

with open("foto.jpg", "rb") as f:
    data = f.read()

url = client.upload_file(data, file_type=FileType.PICTURE, file_name="foto.jpg")

client.send_image_message(
    to_phone="5387654321",
    url=url,
    file_name="foto.jpg",
    file_size=len(data),
    width=800, height=600,
    caption="Mi foto"
)
```

### Descargar archivo

```python
size, path = client.download_file_to_folder(
    url="https://...",
    folder="./descargas/",
    filename="documento.pdf"
)
print(f"Descargado {size} bytes en {path}")
```

## Grupos

```python
# Unirse
client.groups.join("id_del_grupo", nickname="MiApodo")

# Enviar mensaje
client.groups.send_message("id_del_grupo", "Hola a todos")

# Obtener miembros
msg_id = client.groups.get_members("id_del_grupo")

# Expulsar
client.groups.kick_member("id_del_grupo", "5351111111")
```

## Perfil

```python
client.update_profile(alias="MiNombre", bio="Desarrollador Python")

profile_url, thumb_url = client.upload_avatar_from_file("avatar.jpg")
client.update_profile(picture_url=profile_url, thumbnail_url=thumb_url)
```

## Estados (Historias)

```python
import json

content = {"type": "text", "text": "Mi estado", "background": "#2563eb"}
client.publish_status(json.dumps(content))
client.follow_user("5312345678")
```

!!! note "Mensajes asíncronos"

    Métodos como `get_members` y `get_invite_link` son asíncronos. La respuesta llega por el callback de `listen_messages`. Usa `groups.parse_members_response(msg["raw"])` para extraer los datos.
