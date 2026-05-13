# todus-lib

Librería Python para interactuar con la API de **ToDus** (mensajería cubana).

## Instalación

```bash
pip install todus-lib
```

O copia la carpeta `todus/` a tu proyecto.

## Uso rápido

```python
from todus import ToDusClient2, FileType

# Cliente stateful (auto-login, auto-reconnect)
client = ToDusClient2(phone_number="535xxxxxxx", password="tu-password")
client.login()

# Enviar mensaje
client.send_message("535yyyyyyy", "¡Hola desde todus-lib!")

# Escuchar mensajes entrantes
def on_message(msg):
    print(f"[{msg['from']}] {msg['body']}")
    if msg['body'].lower() == "hola":
        client.send_message(msg['from'].split("@")[0], "¡Hola! 👋")

client.listen_messages(on_message)
```

## Auth (primera vez)

```python
client = ToDusClient2(phone_number="535xxxxxxx")
client.request_code()  # Te llega SMS
pin = input("PIN: ")
client.validate_code(pin)  # Guarda password en client.password
print(f"Password: {client.password}")
```

## Archivos

```python
# Subir
with open("foto.jpg", "rb") as f:
    url = client.upload_file(f.read(), FileType.PICTURE)
print(f"URL: {url}")

# Descargar
size = client.download_file(url, "foto_descargada.jpg")
```

## Estructura

```
todus/
├── __init__.py      # Exports principales
├── client.py        # ToDusClient, ToDusClient2
├── parser.py        # Parseo de stanzas XMPP
├── stanza.py        # Constructor de stanzas
├── types.py         # Enums (FileType, ChatState...)
├── errors.py        # Excepciones
├── util.py          # Utilidades
└── constants.py     # Constantes del protocolo
```

## Protocolo descubierto

- **Auth**: HTTP protobuf a `auth.todus.cu`
- **Mensajería**: XMPP custom sobre SSL en `im.todus.cu:5222`
- **Stanzas**: `<m>` (ToDus) en vez de `<message>` (estándar)
- **Archivos**: HTTP PUT/GET con URLs reservadas vía XMPP

## Licencia

MIT
