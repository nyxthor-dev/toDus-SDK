# Tipos y Constantes

## Constantes

```python
XMPP_HOST = "im.todus.cu"
XMPP_PORT = 5222
MUCLIGHT_HOST = "muclight.im.todus.cu"
AUTH_VERSION_NAME = "2.1.2"
AUTH_VERSION_CODE = "30102"
BUFFER_SIZE = 1024 * 1024
KEEPALIVE_INTERVAL = 25
DEFAULT_TIMEOUT = 15
```

## FileType (IntEnum)

| Miembro | Valor | Descripción |
|---------|-------|-------------|
| `FILE` | 0 | Archivo genérico |
| `VOICE` | 1 | Nota de voz |
| `AUDIO` | 2 | Audio |
| `VIDEO` | 3 | Video |
| `PICTURE` | 4 | Imagen |
| `PROFILE` | 5 | Avatar de perfil |
| `PROFILE_THUMBNAIL` | 6 | Miniatura de avatar |

## ChatState (StrEnum)

| Miembro | Valor |
|---------|-------|
| `COMPOSING` | `"composing"` |
| `PAUSED` | `"paused"` |
| `ACTIVE` | `"active"` |
| `GONE` | `"gone"` |
| `INACTIVE` | `"inactive"` |

## MessageType (StrEnum)

| Miembro | Valor |
|---------|-------|
| `CHAT` | `"chat"` |
| `GROUPCHAT` | `"groupchat"` |
| `ERROR` | `"error"` |
| `HEADLINE` | `"headline"` |
| `NORMAL` | `"normal"` |

## PresenceShow (StrEnum)

| Miembro | Valor |
|---------|-------|
| `CHAT` | `"chat"` |
| `AWAY` | `"away"` |
| `XA` | `"xa"` |
| `DND` | `"dnd"` |

## ButtonSize (StrEnum)

| Miembro | Valor | Descripción |
|---------|-------|-------------|
| `FULL` | `"0.82"` | Ancho completo |
| `HALF` | `"0.5"` | Mitad de ancho |

## ButtonCommand (StrEnum)

| Miembro | Valor | Descripción |
|---------|-------|-------------|
| `SEND` | `"cmd_type_send"` | Envía texto al chat |
| `URL` | `"cmd_type_url"` | Abre URL |
| `COPY` | `"cmd_type_copy"` | Copia al portapapeles |
| `CALL` | `"cmd_type_call"` | Inicia llamada |