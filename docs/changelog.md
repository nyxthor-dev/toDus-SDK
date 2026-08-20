# Changelog

## 1.6.0

### Corregido

- `from_phone` filter del EventBus ahora extrae el telefono del JID correctamente
- `download_file` ya no tiene bucle infinito (max_retries=10 con backoff)
- `login()` protobuf: field tags unicos (no duplicado 0x12)
- `listen_messages`: agregado stop_event, backoff exponencial con jitter, max_retries
- Mensajes de grupo ahora incluyen `group_id` y `sender_phone`
- `MessageQueue` retry worker ahora reenvia mensajes correctamente
- `_is_group_target` detecta correctamente numeros con +, prefijos internacionales y JIDs
- `ChannelMixin` ya no hereda de `ToDusClientBase`
- `sticker_hash` y `contact_phone` ahora son XML-escaped
- Parser deduplica por `msg_id` en vez de string completo
- `generate_blurhash` varia segun dimensiones
- `sasl_auth` type hint corregido a `bytes`
- `download_file_to_folder` no destruye descargas parciales
- URLs en `pyproject.toml` apuntan a `nyxthor-dev/toDus-API`

### Agregado

- Modulo `ratelimit.py` con RateLimiter integrado (30 ops/60s por defecto)
- `get_message_history()` con soporte MAM
- 47 tests (0 fallidos)

## 1.5.4

- Event Bus con filtros, prioridades y stop propagation
- Decorador `@client.events.on()`

## 1.5.3

- Cola persistente con SQLite (MessageStore, MessageQueue)
- `ToDusClientWithQueue`
- Callbacks de entrega y fallo

## 1.5.2

- Mensajes programados (scheduler)
- SSL configurable
- Backoff exponencial en reconexion

## 1.5.0

- Privacy, Block, Last Seen, Location, Call mixins

## 1.4.7

- Estados/Historias (ToDusStatusMixin)

## 1.4.6

- Canales (ToDusChannelMixin)

## 1.4.0

- Administracion de grupos MUC Light

## 1.3.0

- Soporte completo para grupos
- Arquitectura de mixins
- pyproject.toml (PEP 621)

## 1.2.0

- Stickers, contactos, botones
- Edicion y eliminacion de mensajes
- Parser incremental

## 1.1.0

- Imagenes y videos con metadata
- Subida/descarga de archivos
- Perfil de usuario

## 1.0.0

- Cliente XMPP basico
- Autenticacion SMS + JWT
- Envio/recepcion de mensajes