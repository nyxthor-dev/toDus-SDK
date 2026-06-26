# 🛠️ Solución de Problemas

Guía rápida para resolver problemas comunes con el SDK toDus.

## Problemas de Conexión

### "ConnectionLostError: Conexión XMPP perdida"

**Causa:** La conexión con el servidor XMPP se cerró inesperadamente.

**Soluciones:**

```python
from todus import ToDusClientWithQueue
from todus.errors import ConnectionLostError
import time

client = ToDusClientWithQueue("5312345678", "password")
client.login()

def on_message(msg):
    print(f"Mensaje: {msg.get('body')}")

# Con reintentos automáticos
max_retries = 5
retry_count = 0

while retry_count < max_retries:
    try:
        client.listen_messages(client.token, on_message)
    except ConnectionLostError as e:
        retry_count += 1
        wait_time = min(2 ** retry_count, 60)  # Backoff exponencial
        print(f"Conexión perdida. Reintentando en {wait_time}s... (intento {retry_count})")
        time.sleep(wait_time)
        # Reauthenticar si es necesario
        try:
            client.login()
        except Exception as e:
            print(f"Error al reauthenticar: {e}")
```

### "timeout occurred"

**Causa:** El servidor tardó demasiado en responder.

**Soluciones:**

```python
# Aumentar timeout en el cliente
client = ToDusClient2(
    phone_number="5312345678",
    password="password",
    timeout=30  # Aumentar de 15s a 30s
)

# O si usas proxy
client = ToDusClient2(
    phone_number="5312345678",
    password="password",
    proxy="socks5://proxy:1080",
    timeout=45
)
```

---

## Problemas de Autenticación

### "AuthenticationError: Invalid credentials"

**Causa:** Las credenciales son incorrectas.

**Soluciones:**

```python
# 1. Verificar el formato del teléfono
from todus.util import normalize_phone

phone = normalize_phone("+5351234567")  # "5351234567"
print(phone)

# 2. Usar contraseña correcta (sin espacios)
client = ToDusClient2(
    phone_number=phone,
    password="mi_contraseña".strip()
)

# 3. Si usas SMS, validar el código
client = ToDusClient()
client.request_code(phone)
code = input("Código: ").strip()
token = client.validate_code(phone, code)
```

### "TokenExpiredError"

**Causa:** El token JWT expiró.

**Soluciones:**

```python
from todus.errors import TokenExpiredError

try:
    client.send_message("5387654321", "Hola")
except TokenExpiredError:
    print("Token expirado, reauthenticando...")
    client.login()
    # Reintentar la operación
    client.send_message("5387654321", "Hola")
```

---

## Problemas de Mensajes

### "Mensaje no se envía / queda en PENDING"

**Causa:** Error de conexión o token inválido.

**Soluciones:**

```python
from todus import ToDusClientWithQueue

client = ToDusClientWithQueue("5312345678", "password")
client.login()

# 1. Registrar callbacks para monitorear estado
def on_delivered(msg):
    print(f"✅ Entregado: {msg.msg_id}")

def on_failed(msg):
    print(f"❌ Falló: {msg.msg_id}")
    print(f"Error: {msg.last_error}")

client.register_on_message_delivered(on_delivered)
client.register_on_message_failed(on_failed)

# 2. Enviar y verificar estado
msg_id = client.send_message_queued("5387654321", "Hola")

# 3. Verificar estadísticas de cola
stats = client.get_queue_stats()
print(f"Pendientes: {stats['pending']}")
print(f"Fallidos: {stats['failed']}")

# 4. Limpiar cola si es necesario
if stats['failed'] > 10:
    client.cleanup_queue()
```

### "MessageError: Destinatario inválido"

**Causa:** El número de teléfono del destinatario es inválido o no existe.

**Soluciones:**

```python
from todus.util import normalize_phone, build_jid

# Validar formato
phone = "5351234567"
phone = normalize_phone(phone)  # Normalizar
jid = build_jid(phone)  # Construir JID
print(f"JID válido: {jid}")

# Usar directamente
client.send_message(phone, "Hola")
```

### "Reply-to message not found"

**Causa:** Intentas responder a un mensaje que no existe o fue eliminado.

**Soluciones:**

```python
# No enviar reply_to_id si no estás seguro
msg_id = client.send_message("5387654321", "Hola")

# O validar que el mensaje existe
def on_message(msg):
    if msg.get('id'):  # El mensaje tiene ID
        client.send_message("5387654321", "Respuesta", reply_to_id=msg['id'])
```

---

## Problemas con Archivos

### "UploadError: Upload failed"

**Causa:** Error al subir archivo a los servidores.

**Soluciones:**

```python
from todus.types import FileType

client.login()

# 1. Verificar archivo existe
import os
file_path = "documento.pdf"
if not os.path.exists(file_path):
    print(f"Archivo no encontrado: {file_path}")
else:
    file_size = os.path.getsize(file_path)
    print(f"Tamaño: {file_size} bytes")

# 2. Subir con progreso
def progress(current, total):
    percent = (current / total) * 100
    print(f"Subiendo: {percent:.1f}%")

with open(file_path, "rb") as f:
    data = f.read()

try:
    url = client.upload_file(
        data,
        file_type=FileType.FILE,
        progress_callback=progress,
        file_name="documento.pdf"
    )
    print(f"✅ Subido: {url}")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Si sigue fallando, reintentar
import time
max_retries = 3
for attempt in range(max_retries):
    try:
        url = client.upload_file(data, FileType.FILE, file_name="documento.pdf")
        break
    except Exception as e:
        print(f"Intento {attempt+1} falló: {e}")
        time.sleep(2)
```

### "Descarga no funciona"

**Causa:** URL inválida o acceso denegado.

**Soluciones:**

```python
# 1. Obtener URL real
url = client.get_real_download_url(file_url)
print(f"URL real: {url}")

# 2. Descargar a carpeta
import os
folder = os.path.expanduser("~/descargas/")
os.makedirs(folder, exist_ok=True)

try:
    size, path = client.download_file_to_folder(url, folder)
    print(f"✅ Descargado: {path} ({size} bytes)")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Con reintentos
for attempt in range(3):
    try:
        size, path = client.download_file_to_folder(url, folder)
        break
    except Exception as e:
        print(f"Intento {attempt+1} falló")
        time.sleep(2)
```

---

## Problemas con Grupos

### "GroupError: No puedo unirme al grupo"

**Causa:** Grupo no existe, estás baneado o invitación expiró.

**Soluciones:**

```python
from todus.errors import GroupError

try:
    client.groups.join("id_del_grupo", nickname="MiApodo")
except GroupError as e:
    print(f"Error: {e}")
    
    # Opciones:
    # 1. Solicitar enlace de invitación al administrador
    # 2. Crear un grupo nuevo
    # 3. Verificar que el ID es correcto
```

### "No recibo mensajes del grupo"

**Causa:** No estás suscrito o hay error de parsing.

**Soluciones:**

```python
# 1. Verificar que estás en el grupo
groups = client.groups.get_my_groups()

# 2. Escuchar mensajes de grupo explícitamente
def on_message(msg):
    if msg.get('is_group'):
        print(f"Grupo {msg['group_id']}: {msg.get('body')}")
    else:
        print(f"Privado de {msg['from']}: {msg.get('body')}")

client.listen_messages(client.token, on_message)

# 3. Registrar callback específico del grupo
def on_group_message(msg):
    print(f"Mensaje del grupo: {msg.get('body')}")

client.groups.on_group_message("id_del_grupo", on_group_message)
```

---

## Problemas de Rendimiento

### "Cola muy lenta / Muchos mensajes pendientes"

**Causa:** Worker de reintentos saturado o conexión inestable.

**Soluciones:**

```python
# 1. Revisar estadísticas
stats = client.get_queue_stats()
print(f"Pendientes: {stats['pending']}")
print(f"Fallidos: {stats['failed']}")

# 2. Pausar el worker si es necesario
client.queue.stop_auto_retry_worker()
print("Worker pausado")

# 3. Limpiar mensajes antiguos
deleted = client.cleanup_queue()
print(f"Limpiados: {deleted} mensajes")

# 4. Reanudar el worker
client.queue.start_auto_retry_worker()

# 5. Ajustar reintentos máximos
# En todus/cache/store.py
# max_retries = 2  (en vez de 3 o más)
```

### "Alto uso de memoria"

**Causa:** Muchos listeners activos o cache de stanzas.

**Soluciones:**

```python
# 1. Limpiar cache si exite
# (Depende de tu versión específica)

# 2. No crear múltiples clientes innecesarios
# ❌ Malo:
for i in range(100):
    client = ToDusClient2(phone, password)

# ✅ Bien:
client = ToDusClient2(phone, password)
client.login()
# Reutilizar un solo cliente

# 3. Usar generadores en lugar de listas
# ❌ Malo:
messages = [process(msg) for msg in big_list]

# ✅ Bien:
def process_messages():
    for msg in big_list:
        yield process(msg)
```

---

## Habilitando Debug

Para ver logs detallados:

```python
import logging

# Configurar logging a DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ahora los logs del SDK aparecerán
from todus import ToDusClient2

client = ToDusClient2("5312345678", "password")
client.login()  # Verás logs detallados
```

---

## Reportar Problemas

Si no encuentras solución:

1. **Activa logs DEBUG** (ver arriba)
2. **Recopila:**
   - Versión del SDK: `python -c "import todus; print(todus.__version__)"`
   - Versión de Python: `python --version`
   - Sistema operativo
   - Logs completos del error
3. **Abre un issue en** [GitHub](https://github.com/vm1008079-web/toDus-API/issues)

**Información a incluir:**

```markdown
- **SDK Version:** 1.5.2
- **Python Version:** 3.11
- **OS:** Linux/Windows/Mac
- **Error:** [Descripción detallada]
- **Código reproducible:**
```python
# Tu código aquí
```
- **Logs:** [Salida con DEBUG enabled]
```

---

## Recursos Útiles

- 📖 [Documentación completa](/)
- 💬 [Discord/Chat de la comunidad](https://discord.gg/todus)
- 🐛 [Issues en GitHub](https://github.com/vm1008079-web/toDus-API/issues)
- 📝 [CHANGELOG](changelog.md)
