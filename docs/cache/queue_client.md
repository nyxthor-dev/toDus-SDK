# Cliente con Cola

`ToDusClientWithQueue` combina todas las capacidades de `ToDusClient2` con la cola persistente.

## Constructor

```python
ToDusClientWithQueue(
    phone_number: str,
    password: str = "",
    enable_queue: bool = True,
    queue_db_path: Optional[str] = None,
    **kwargs
)
```

- `phone_number` — Número de teléfono (formato `53XXXXXXXX`)
- `password` — Contraseña de la cuenta
- `enable_queue` — Activa la cola (por defecto `True`)
- `queue_db_path` — Ruta SQLite, por defecto `~/.todus/messages.db`

## send_message_queued

```python
msg_id = client.send_message_queued("5387654321", "Mensaje con garantía")
```

Flujo interno:

1. Detecta si el destino es privado o grupo
2. Envía el mensaje
3. Lo encola en SQLite
4. Si falla, el worker lo reintentará automáticamente

## Callbacks

```python
def on_delivered(msg):
    print(f"Entregado: {msg.msg_id}")

def on_failed(msg):
    print(f"Falló: {msg.msg_id} - {msg.last_error}")

client.register_on_message_delivered(on_delivered)
client.register_on_message_failed(on_failed)
```

## Estadísticas

```python
stats = client.get_queue_stats()
# {'pending': 0, 'sent': 2, 'delivered': 5, 'read': 3, 'failed': 1}
```

## Limpieza

```python
deleted = client.cleanup_queue()  # Elimina READ/DELIVERED > 30 días
```

## Ejemplo con archivos

```python
from todus import ToDusClientWithQueue
from todus.types import FileType

client = ToDusClientWithQueue("5312345678", "password")
client.login()

data = open("foto.jpg", "rb").read()
url = client.upload_file(data, file_type=FileType.PICTURE, file_name="foto.jpg")

# Enviar archivo por chat privado
client.send_image_message(
    to_phone="5387654321", url=url, file_name="foto.jpg",
    file_size=len(data), width=800, height=600, caption="Foto"
)

# O encolar texto con callback
client.register_on_message_delivered(lambda m: print("Entregado"))
client.send_message_queued("5387654321", "Mira la foto")
```

!!! note

    El worker de reintentos corre en un hilo daemon y se detiene al finalizar el programa. Para detenerlo manualmente: `client.queue.stop_auto_retry_worker()`.