# todus-lib

**Cliente Python para ToDus** — la plataforma de mensajería instantánea cubana. Soporta chat privado, grupos MUC Light, archivos, imágenes, videos, stickers, botones interactivos y más.

> **Versión:** 1.3.0  
> **Python:** >= 3.8  
> **Autor:** OrionWolf

---

## 📦 Instalación

```bash
pip install requests
python setup.py install
```

O directamente desde la carpeta:

```bash
pip install -e .
```

---

## 🚀 Uso Rápido

### 1. Cliente stateful (recomendado)

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="535xxxxxxx", password="tu_password")
client.login()

# Enviar mensaje de texto
client.send_message("535yyyyyyy", "¡Hola desde Python!")

# Enviar imagen
client.send_image_message(
    "535yyyyyyy",
    url="https://...",
    file_name="foto.jpg",
    file_size=102400
)
```

### 2. Autenticación por primera vez (SMS)

```python
client = ToDusClient2(phone_number="535xxxxxxx")
client.request_code()          # Recibes SMS con PIN
client.validate_code("123456") # Guarda client.password
print("Guarda esta contraseña:", client.password)
client.login()
```

### 3. Escuchar mensajes

```python
def on_message(msg):
    print(f"De: {msg['from']} — {msg['body']}")

client.listen_messages(on_message)
```

---

## 📁 Estructura del Proyecto

```
todus-lib/
├── todus/                  # Código fuente de la librería
│   ├── __init__.py         # Exports principales
│   ├── client.py           # ToDusClient y ToDusClient2
│   ├── group.py            # Soporte para grupos MUC Light
│   ├── stanza.py           # Constructor de stanzas XMPP
│   ├── parser.py           # Parser incremental de stanzas
│   ├── types.py            # Enums (FileType, ChatState, etc.)
│   ├── util.py             # Utilidades (JID, XML, JWT, etc.)
│   ├── constants.py        # Hosts, puertos, versiones
│   ├── errors.py           # Excepciones personalizadas
│   └── setup.py            # Configuración de setuptools
├── examples/               # Ejemplos de uso
│   └── bot.py              # Bot con comando /start
└── README.md               # Este archivo
```

---

## 🤖 Bot de Ejemplo

En [`examples/bot.py`](examples/bot.py) encontrás un bot funcional con los comandos:

| Comando | Descripción |
|---------|-------------|
| `/start` | Mensaje de bienvenida con lista de comandos |
| `/info`  | Información sobre la librería |
| `/ping`  | Responde "pong" |

### Ejecutar el bot:

```bash
export TODUS_PHONE=535xxxxxxx
export TODUS_PASSWORD=tu_password
python examples/bot.py
```

El bot responde automáticamente a cualquier mensaje con un eco, salvo que sea uno de los comandos anteriores.

---

## 📡 Tipos de Mensaje Soportados

| Tipo | Método (ToDusClient2) |
|------|----------------------|
| Texto | `send_message(to, body)` |
| Imagen | `send_image_message(to, url, file_name, file_size, ...)` |
| Video | `send_video_message(to, url, video_id, file_name, ...)` |
| Archivo | `send_file_message(to, url, file_type, ...)` |
| Sticker | `send_sticker_message(to, sticker_id, ...)` |
| Contacto | `send_contact_message(to, contact_id, ...)` |
| Botones | `send_button_message(to, text, buttons)` |
| Editar | `edit_message(to, new_body, original_msg_id)` |
| Eliminar | `delete_message(to, message_id)` |

> **Auto-detección de destino:** si el `to` no es un número cubano (10 dígitos empezando por 53), se asume que es un `group_id` y el mensaje se envía al grupo automáticamente.

---

## 👥 Grupos MUC Light

```python
# Unirse a un grupo
client.groups.join("mi-grupo-id")

# Enviar mensaje a grupo (auto-detectado)
client.send_message("mi-grupo-id", "Hola grupo!")

# Callback específico por grupo
client.groups.on_group_message("mi-grupo-id", lambda m: print(m))
```

---

## 📤 Subir y Descargar Archivos

```python
# Subir
with open("foto.jpg", "rb") as f:
    url = client.upload_file(f.read(), FileType.PICTURE)

# Descargar
size, path = client.download_file_to_folder(url, "./descargas")
```

---

## ⚠️ Excepciones

| Excepción | Cuándo ocurre |
|-----------|---------------|
| `AuthenticationError` | Credenciales inválidas o falta autenticación |
| `TokenExpiredError` | El token JWT expiró |
| `ConnectionLostError` | Se perdió la conexión XMPP |
| `UploadError` | Error al subir/descargar archivo |
| `GroupError` | Error en operación de grupo |
| `ParseError` | Stanza malformada |

---

## 🔗 Recursos

- **ToDus oficial:** https://todus.cu  
- **Apklis:** https://www.apklis.cu/application/cu.todus.android  
- **Cliente CLI original (adbenitez):** https://github.com/adbenitez/todus

---

## 📄 Licencia

MIT License
