<div align="center">

# 📡 OrionDus ✉️

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDZ3NW84eDhzNm1xd3pjOXNuMWQwbTlvdGhleWdicXgwNmNhMmQ5ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/qgQUggAC3Pfv687qPC/giphy.gif" width="480" alt="todus-lib banner"/>

**Cliente Python no oficial para ToDus — la plataforma de mensajería cubana**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Version](https://img.shields.io/badge/version-1.0.0-green?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)
![Status](https://img.shields.io/badge/status-Beta-orange?style=flat-square)

</div>

---

## 📖 Información General

`todus-lib` es una librería Python que implementa el protocolo de **ToDus**, la aplicación de mensajería más utilizada en Cuba. Permite a los desarrolladores interactuar programáticamente con la plataforma mediante autenticación HTTP/Protobuf y mensajería en tiempo real vía XMPP sobre SSL.

- **Protocolo de autenticación:** HTTP + Protobuf (`auth.todus.cu`)
- **Mensajería en tiempo real:** XMPP sobre SSL (`im.todus.cu:5222`)
- **Transferencia de archivos:** HTTP con soporte de reanudación
- **Versión simulada:** `0.40.29` (código `21833`)

---

## ✨ Características

- 🔐 **Autenticación completa** — Registro con PIN SMS, validación de código y login con JWT
- 💬 **Envío y recepción de mensajes** — Mensajes de texto en tiempo real vía XMPP
- 📎 **Soporte multimedia** — Envío y recepción de imágenes, audio, video, voz y archivos genéricos
- ⬆️ **Subida de archivos** — Upload directo con resolución de URL via XMPP
- ⬇️ **Descarga con reanudación** — Descarga robusta con soporte de archivos parciales (`.part`)
- 🔄 **Auto-reconexión** — `ToDusClient2` gestiona token expirado y pérdida de conexión automáticamente
- 📡 **Escucha de mensajes en tiempo real** — Listener con callback y bucle de reconexión
- 🧩 **Estados de chat XEP-0085** — `composing`, `paused`, `active`, `gone`, `inactive`
- 🪝 **Manejo de errores tipado** — Jerarquía de excepciones específicas del dominio
- 🧵 **Thread-safe** — Arquitectura stateless pensada para uso concurrente

---

## 🚀 Instalación

```bash
git clone https://github.com/tu-usuario/todus-lib.git
cd todus-lib
pip install -e .
```

O directamente como dependencia:

```bash
pip install todus-lib
```

---

## 💡 Ejemplos de Uso

### Registro de nuevo usuario

```python
from todus import ToDusClient

client = ToDusClient()

# 1. Solicitar PIN por SMS
client.request_code("53XXXXXXXX")

# 2. Validar el PIN recibido y obtener contraseña
password = client.validate_code("53XXXXXXXX", "123456")
print(f"Contraseña: {password}")
```

---

### Login y envío de mensaje

```python
from todus import ToDusClient

client = ToDusClient()
token = client.login("53XXXXXXXX", "mi_password_96chars")

client.send_message(token, "53YYYYYYYY@im.todus.cu", "¡Hola desde todus-lib!")
```

---

### Cliente stateful con auto-reconexión

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="53XXXXXXXX", password="mi_password")
client.login()

# Enviar mensaje
client.send_message("53YYYYYYYY", "¡Hola!")

# Escuchar mensajes entrantes
def on_message(msg: dict):
    print(f"[{msg['from']}]: {msg['body']}")

client.listen_messages(callback=on_message)  # bucle con auto-reconexión
```

---

### Subir y enviar un archivo

```python
from todus import ToDusClient2
from todus.types import FileType

client = ToDusClient2("53XXXXXXXX", "mi_password")
client.login()

with open("foto.jpg", "rb") as f:
    url = client.upload_file(f.read(), file_type=FileType.PICTURE)

client.send_file_message(
    to_phone="53YYYYYYYY",
    url=url,
    file_type=FileType.PICTURE,
    caption="Mi foto 📸"
)
```

---

### Descargar un archivo

```python
size, path = client.download_file_to_folder(
    url="https://storage.todus.cu/...",
    folder="./descargas",
    filename="video.mp4"
)
print(f"Descargado: {path} ({size} bytes)")
```

---

## 📦 Estructura del Proyecto

```
todus-lib/
├── todus/
│   ├── __init__.py        # Exportaciones públicas
│   ├── client.py          # ToDusClient y ToDusClient2
│   ├── constants.py       # Hosts, puertos y timeouts
│   ├── errors.py          # Jerarquía de excepciones
│   ├── parser.py          # Parser XML incremental XMPP
│   ├── stanza.py          # Constructores de stanzas XMPP
│   ├── types.py           # FileType, ChatState, MessageType
│   └── util.py            # Utilidades (JWT, tokens, formato)
└── setup.py
```

---

## 🤝 Colaboradores

¡Gracias a todas las personas que han contribuido a este proyecto!

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/tu-usuario">
        <img src="https://github.com/tu-usuario.png" width="80px;" alt=""/><br />
        <sub><b>tu-usuario</b></sub>
      </a><br/>
      🛠️ Autor principal
    </td>
    <!-- Agrega más colaboradores aquí -->
  </tr>
</table>

> ¿Quieres contribuir? ¡Los PRs son bienvenidos! Abre un issue o envía tu pull request.

---

## ⚠️ Advertencia

Este proyecto es una implementación **no oficial** e **independiente**. No está afiliado, respaldado ni relacionado con los desarrolladores de ToDus. Úsalo bajo tu propia responsabilidad y respetando los términos de servicio de la plataforma.

---

## 📄 Copyright

```
MIT License

Copyright (c) 2024 Community Contributors

Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
de este software y los archivos de documentación asociados, para utilizar el software
sin restricciones, incluyendo sin limitación los derechos de uso, copia, modificación,
fusión, publicación, distribución, sublicencia y/o venta de copias del software,
sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas
las copias o partes sustanciales del software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO.
```

---

<div align="center">
  Hecho con ❤️ por la comunidad • <a href="https://github.com/tu-usuario/todus-lib/issues">Reportar un bug</a> • <a href="https://github.com/tu-usuario/todus-lib/pulls">Contribuir</a>
</div>
