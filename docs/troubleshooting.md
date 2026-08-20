# Solución de Problemas

## Conexión

### Conexión XMPP perdida

`listen_messages` reintenta automáticamente con backoff exponencial. Si necesitas control manual:

```python
from todus.errors import ConnectionLostError

try:
    client.listen_messages(on_message)
except ConnectionLostError:
    client.login()
    client.listen_messages(on_message)
```

### Timeout

Aumenta el timeout del cliente:

```python
client = ToDusClient2("5312345678", "password", timeout=30)
```

## Autenticación

### Credenciales inválidas

Verifica el formato del teléfono:

```python
from todus.util import normalize_phone
phone = normalize_phone("+5351234567")  # "5351234567"
```

### Token expirado

```python
from todus.errors import TokenExpiredError

try:
    client.send_message("5387654321", "Hola")
except TokenExpiredError:
    client.login()
    client.send_message("5387654321", "Hola")
```

## Mensajes

### Mensaje no se envía

Registra callbacks para monitorear el estado:

```python
client.register_on_message_failed(lambda m: print(f"Falló: {m.last_error}"))
client.register_on_message_delivered(lambda m: print(f"Entregado: {m.msg_id}"))

stats = client.get_queue_stats()
print(stats)
```

### Destinatario inválido

```python
from todus.util import normalize_phone, build_jid
phone = normalize_phone("5351234567")
print(build_jid(phone))  # "5351234567@im.todus.cu"
```

## Archivos

### Error al subir

```python
from todus.types import FileType

with open("archivo.pdf", "rb") as f:
    data = f.read()

url = client.upload_file(data, FileType.FILE, file_name="archivo.pdf")
```

### Descarga falla

Obtén la URL real antes de descargar:

```python
real_url = client.get_real_download_url(file_url)
size, path = client.download_file_to_folder(real_url, "./descargas/")
```

## Grupos

### No puedo unirme

```python
from todus.errors import GroupError

try:
    client.groups.join("id_del_grupo", nickname="MiApodo")
except GroupError as e:
    print(f"Error: {e}")
```

### No recibo mensajes del grupo

Verifica que el callback maneja `is_group`:

```python
def on_message(msg):
    if msg.get('is_group'):
        print(f"Grupo {msg['group_id']}: {msg.get('body')}")
```

## Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
```

## Reportar problemas

Abre un issue en [GitHub](https://github.com/nyxthor-dev/toDus-API/issues) incluyendo:

- Versión del SDK y Python
- Sistema operativo
- Código que reproduce el error
- Logs con DEBUG activado
