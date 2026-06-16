📱 todus-lib

Cliente Python para ToDus — la plataforma de mensajería instantánea cubana. Soporta chat privado, grupos MUC Light, archivos, imágenes, videos, stickers, botones interactivos y más.

Versión: 1.3.0
Python: >= 3.8
Autor: OrionWolf

---

📦 Instalación

```bash
pip install requests
python setup.py install
```

O directamente desde la carpeta:

```bash
pip install -e .
```

---

🔐 Autenticación (¡Importante!)

ToDus no usa contraseñas elegidas por el usuario. El proceso de autenticación tiene dos pasos:

1. Obtener un token largo (96 caracteres) mediante validación por SMS.
2. Usar ese token para hacer login y obtener un JWT de sesión, que se usa para todas las comunicaciones.

El cliente ToDusClient2 guarda ese token largo en el atributo password (nombre histórico), pero en la práctica debes entenderlo como auth_token.

🔹 Flujo para primera vez (SMS)

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="535xxxxxxx")  # sin password aún

# 1. Pedir código SMS
client.request_code()   # te llega un PIN de 6 dígitos

# 2. Validar el código
client.validate_code("123456")
# Ahora client.password contiene el token largo (96 caracteres)
# ¡Guárdalo en un lugar seguro para futuras sesiones!

# 3. Obtener el JWT de sesión
client.login()   # ahora client.logged == True
```

🔹 Si ya tienes el token largo (de una sesión anterior)

```python
client = ToDusClient2(phone_number="535xxxxxxx", password="ese_token_largo_que_guardaste")
client.login()   # obtiene el JWT internamente
```

⚠️ Importante: Nunca pases un JWT directamente al constructor. El cliente se encarga de renovarlo automáticamente cuando expira. El parámetro password espera el token largo de 96 caracteres.

---

🚀 Uso Rápido

Enviar mensajes (privados y grupos automáticamente)

```python
# Asumiendo que ya hiciste login
client.send_message("535yyyyyyy", "¡Hola mundo!")   # privado
client.send_message("mi-grupo-id", "Hola grupo!")   # grupo (auto-detectado)
```

Enviar imagen (con subida previa)

```python
from todus import FileType

# 1. Subir la imagen
with open("foto.jpg", "rb") as f:
    image_data = f.read()
url = client.upload_file(image_data, FileType.PICTURE)

# 2. Enviar el mensaje con la imagen
client.send_image_message(
    "535yyyyyyy",
    url=url,
    file_name="foto.jpg",
    file_size=len(image_data),
    caption="Mi foto"
)
```

Escuchar mensajes entrantes

```python
def on_message(msg):
    if msg.get("body"):
        print(f"{msg['from']}: {msg['body']}")

client.listen_messages(on_message)   # bucle infinito
```

---

🤖 Bot de Ejemplo

En la carpeta examples/ encontrarás un bot funcional con comandos:

Comando Respuesta
/start Mensaje de bienvenida con lista de comandos
/info Información sobre la librería
/ping "pong"

Ejecútalo con:

```bash
export TODUS_PHONE=535xxxxxxx
export TODUS_AUTH_TOKEN=token_largo_de_96_caracteres
python examples/bot.py
```

---

📡 Tipos de Mensaje Soportados

Tipo Método (ToDusClient2)
Texto send_message(to, body)
Imagen send_image_message(to, url, file_name, file_size, ...)
Video send_video_message(to, url, video_id, file_name, ...)
Archivo send_file_message(to, url, file_type, ...)
Sticker send_sticker_message(to, sticker_id, ...)
Contacto send_contact_message(to, contact_id, ...)
Botones send_button_message(to, text, buttons)
Editar edit_message(to, new_body, original_msg_id)
Eliminar delete_message(to, message_id)

Auto-detección de destino: si el to no es un número cubano (10 dígitos empezando por 53), se asume que es un group_id y el mensaje se envía al grupo automáticamente.

---

👥 Grupos MUC Light

```python
# Unirse a un grupo
client.groups.join("mi-grupo-id")

# Enviar mensaje al grupo (auto-detectado)
client.send_message("mi-grupo-id", "Hola grupo!")

# Callback específico para mensajes de ese grupo
def on_group_msg(msg):
    print(f"{msg['sender_phone']}: {msg['body']}")

client.groups.on_group_message("mi-grupo-id", on_group_msg)

# Salir del grupo
client.groups.leave("mi-grupo-id")
```

---

📤 Subir y Descargar Archivos

```python
# Subir cualquier archivo
with open("documento.pdf", "rb") as f:
    url = client.upload_file(f.read(), FileType.FILE)

# Descargar a una carpeta
size, path = client.download_file_to_folder(url, "./descargas")
print(f"Descargado {size} bytes en {path}")
```

---

⚠️ Excepciones

Excepción Cuándo ocurre
AuthenticationError Credenciales inválidas o falta autenticación
TokenExpiredError El token JWT expiró (el cliente lo renueva automáticamente si usas ToDusClient2)
ConnectionLostError Se perdió la conexión XMPP
UploadError Error al subir/descargar archivo
GroupError Error en operación de grupo
ParseError Stanza malformada

---

🗂️ Estructura del Proyecto

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
│   └── bot.py              # Bot con comandos
└── README.md               # Este archivo
```

---

🔗 Recursos

· ToDus oficial: https://web.todus.cu
· Apklis: https://www.apklis.cu/application/cu.todus.android
---

📄 Licencia

MIT License
