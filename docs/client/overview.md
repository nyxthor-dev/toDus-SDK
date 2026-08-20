# Cliente ToDus

El módulo `client` es el núcleo del SDK. Contiene la lógica de conexión XMPP, autenticación y todas las funcionalidades de la plataforma.

## Arquitectura

`ToDusClient2` combina múltiples **mixins** que agrupan funcionalidades específicas:

```
ToDusClient2
├── ToDusClientBase          # Socket XMPP, Handshake, Sesiones
├── ToDusAuthMixin           # Autenticación (login, código SMS)
├── ToDusMessageMixin        # Mensajería (texto, archivos, etc.)
├── ToDusFileMixin           # Subida/descarga de archivos
├── ToDusProfileMixin        # Perfil y avatar
├── ToDusChannelMixin        # Canales públicos/privados
├── ToDusStatusMixin         # Estados/Historias
├── ToDusPrivacyMixin        # Configuración de privacidad
├── ToDusBlockMixin          # Bloqueo de usuarios
├── ToDusLastMixin           # Última conexión
├── ToDusLocationMixin       # Ubicación (Near)
└── ToDusCallMixin           # Señalización de llamadas
```

## Clases principales

### ToDusClient2 (Recomendado)

Clase **stateful** que mantiene la sesión, el token y el número de teléfono.

```python
ToDusClient2(
    phone_number: str,
    password: str = "",
    proxy: Optional[str] = None,
    verify_ssl: bool = False,
    **kwargs
)
```

**Propiedades:**

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `token` | `str` | JWT actual |
| `logged` | `bool` | Sesión activa |
| `phone_number` | `str` | Número normalizado |
| `groups` | `GroupClient` | Cliente de grupos |

**Métodos principales:**

- `login()` — Inicia sesión
- `send_message(to, body, reply_to_id)` — Envía texto
- `upload_file(data, file_type, progress_callback, file_name)` — Sube archivo
- `listen_messages(callback)` — Bucle de escucha con reconexión automática
- `get_message_history(jid, since, before, limit)` — Historial MAM
- `set_rate_limit(max_ops, window_seconds)` — Configura rate limiter

### ToDusClient (Stateless)

Hereda todos los mixins pero **no** mantiene estado. Todos los métodos requieren `token` como primer argumento. Útil para múltiples cuentas.

```python
client = ToDusClient()
token = client.login("5312345678", "password")
client.send_message(token, "5387654321@im.todus.cu", "Hola")
```

## Detección de grupos

`ToDusClient2` detecta automáticamente si el destino es un grupo o un chat privado:

- Número de teléfono con formato válido → mensaje privado
- Cualquier otro formato (UUID, texto) → se reenvía a `client.groups`

Esto permite usar los mismos métodos (`send_message`, `send_image_message`, etc.) para privados y grupos.

## Ciclo de conexión

1. **Autenticación** — `login()` obtiene el token JWT
2. **Handshake** — Socket XMPP + negociación SASL
3. **Sesión** — Presencia inicial y mantenimiento del stream
4. **Escucha** — `listen_messages()` recibe stanzas en bucle
5. **Keepalive** — Pings cada 25 segundos
6. **Reconexión** — Backoff exponencial con jitter si se pierde la conexión

## Acceso a mixins

Todos los mixins están disponibles directamente en la instancia:

```python
client.send_message(...)       # ToDusMessageMixin
client.upload_file(...)        # ToDusFileMixin
client.update_profile(...)     # ToDusProfileMixin
client.block_user(...)         # ToDusBlockMixin
client.set_location(...)       # ToDusLocationMixin
client.start_call(...)         # ToDusCallMixin
client.publish_status(...)     # ToDusStatusMixin
client.create_channel(...)     # ToDusChannelMixin
```

Consulta [API de Mixins](mixins.md) para la referencia completa de todos los métodos.
