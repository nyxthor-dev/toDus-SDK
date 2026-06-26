# 📝 Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [1.5.4] - 2026-06-26

### 🎉 Agregado
- **Event Bus y Sistema de Filtros Avanzados**: Nuevo módulo `todus/events/` con dispatcher centralizado de eventos:
  - ✅ `EventBus`: Gestor thread-safe con prioridades y control de propagación
  - ✅ `Filter` + `build_filter`: Filtros declarativos (from_phone, contains_keyword, regex, custom, etc.)
  - ✅ Decorador `@client.events.on(event_type, **filters)` para handlers limpios
  - ✅ Handlers wildcard (`'*'`) que capturan todos los eventos
  - ✅ Despacho automático de 7 tipos: `message`, `presence`, `receipt`, `iq`, `tdack`, `deleted`, `chat_state`
  - ✅ Método `handle_parsed_stanza()` para procesar stanzas
  - ✅ Documentación completa en `docs/events/overview.md`

### 📝 Cambiado
- `ToDusClient` ahora inicializa automáticamente `self.events = EventBus()`
- `_listen_loop` refactorizada para usar EventBus y despachar eventos
- Actualización de mkdocs.yml: nueva sección "🎯 Event Bus y Filtros"
- Nuevo ejemplo: "Bot Reactivo con EventBus" en ejemplos avanzados

### 🔧 Corregido
- Thread-safety en dispatch con `RLock`
- Manejo robusto de excepciones (logging sin ruptura)

### 🧪 Tests
- ✅ 5 tests en `test_events.py` (filtros, prioridades, wildcard)
- ✅ Integración cliente en `test_client_events.py` (7 tipos de eventos)

---

## [1.5.3] - 2026-06-21

### 🎉 Agregado
- **Message Queue System**: Nuevo módulo `todus/cache/` con almacenamiento persistente SQLite:
  - `MessageStore`: CRUD thread-safe con índices optimizados
  - `MessageQueue`: Cola con reintentos automáticos y backoff exponencial
  - `MessageQueueMixin`: Mixin para cualquier cliente
  - `ToDusClientWithQueue`: Cliente completo con queue integrado
  - Ciclo de vida: pending → sent → delivered → read/failed
  - Callbacks de evento: `on_message_sent`, `on_message_delivered`, `on_message_read`, `on_message_failed`
  - Método `get_queue_stats()` para monitoreo

### 📝 Cambiado
- Optimización en `ToDusClient2`: eliminadas ~200 líneas de código duplicado
- `listen_messages` soporta `max_retries` configurable con backoff exponencial
- Nuevo `__all__` en `todus/__init__.py` con MessageQueue exports

### 🔧 Corregido
- Bug SQL: escapada columna `"to"` en queries
- Thread-safety mejorada con RLock en MessageStore
- Limpieza automática de mensajes antiguos (30+ días)

---

## [1.5.2] - 2026-06-20

### 🎉 Agregado
- **Sistema de Mensajes Programados (Scheduler)**:
  - `send_later(to, body, delay)`: envío con retraso
  - `schedule_daily(to, body, hour, minute)`: mensajes diarios
  - `schedule_interval(to, body, interval)`: intervalos regulares
  - `cancel_task(task_id)`: cancelar tareas
  - `get_scheduler_stats()`: estadísticas
- **Verificación SSL configurable**: Nuevo parámetro `verify_ssl`
- **Backoff exponencial con jitter**: reconexiones inteligentes (1s → 60s max)

### 📝 Cambiado
- Refactorización de `ToDusClient2` con método interno `_send_to_target`
- Seguridad SSL mejorada (activable)

### 🔧 Corregido
- Reconexiones más eficientes (backoff vs sleep fijo)
- Eliminación de duplicación de código

---

## [1.5.1] - 2024-06-20

### 🔧 Corregido
- Corrección de la rama de la documentación

---

## [1.5.0] - 2024-06-20

### 🎉 Agregado
- **Cobertura 100% de la API de ToDus**:
  - **Privacidad** (`ToDusPrivacyMixin`): `get_profile_privacy`, `set_profile_privacy`
  - **Bloqueos** (`ToDusBlockMixin`): `block_user`, `unblock_user`, `get_block_list`
  - **Última Conexión** (`ToDusLastMixin`): `get_last_seen`
  - **Ubicación** (`ToDusLocationMixin`): `set_location`, `get_people_near`
  - **Llamadas** (`ToDusCallMixin`): `start_call`, `pickup_call`, `end_call`

---

## [1.4.7] - 2026-06-20

### 🎉 Agregado
- **Estados / Historias de ToDus** (`ToDusStatusMixin`):
  - `publish_status`: publicar historias
  - `delete_status`: eliminar estado
  - `follow_user` / `unfollow_user`: gestión de seguidores
  - `get_followers`, `get_following`: consultar red

---

## [1.4.6] - 2026-06-20

### 🎉 Agregado
- **Canales de ToDus** (`ToDusChannelMixin`):
  - `create_channel`: crear canales
  - `get_my_channels`: listar canales del usuario
  - `publish_to_channel`: publicar mensajes
  - `subscribe_channel`, `leave_channel`: gestión

### 🔧 Corregido
- Problema en actualización de perfil (nombre/alias)

---

## [1.4.5] - 2026-06-20

### 🔧 Corregido
- Test automatizado `test_upload_avatar_uses_session`

---

## [1.4.4] - 2026-06-20

### 🔧 Corregido
- `TypeError` en `upload_avatar`

---

## [1.4.3] - 2026-06-20

### 🎉 Agregado
- Método `set_todus_id` en `ToDusProfileMixin`

---

## [1.4.2] - 2026-06-20

### 📝 Cambiado
- Reescritura de `update_profile` con Protobuf
- Inyección de JWT sin prefijo Bearer

---

## [1.4.1] - 2026-06-20

### 🎉 Agregado
- Namespaces XMPP `x11`, `x13`, `x14` para grupos
- `get_members`, `set_member_role`, `kick_member`
- `get_invite_link`, `revoke_invite_link`

---

## [1.4.0] - 2026-06-20

### 🎉 Agregado
- Administración de grupos MUC Light:
  - `set_name`, `set_subject`, `set_avatar`
  - Gestión de miembros y roles

---

## [1.3.9] - 2026-06-20

### 🔧 Corregido
- Atributo `to` en stanzas (vs `o`)
- Atributo `xmlns='jc'` en video_message

---

## [1.3.8] - 2026-06-20

### 🔧 Corregido
- Parámetro `caption` en stanzas de grupos
- Actualización de versión (AUTH_VERSION_NAME = "2.1.2")

---

## [1.3.7] - 2026-06-20

### 🔧 Corregido
- Normalización de teléfono automática
- Serialización dinámica de protobuf (evita 400 Bad Request)

---

## [1.3.6] - 2026-06-20

### 🔧 Corregido
- Desactivación de verificación SSL para compatibilidad
- Silenciamiento de advertencias `InsecureRequestWarning`

---

## [1.3.5] - 2026-06-20

### 🔧 Corregido
- Optimización de badges en README

### 📝 Cambiado
- Migración a Trusted Publishing (OIDC) en GitHub Actions

---

## [1.3.4] - 2026-06-20

### 🔧 Corregido
- Proxy en subida de archivos y avatares
- Tests unitarios para comportamiento de proxy

---

## [1.3.3] - 2026-06-19

### 📝 Cambiado
- Renombrado paquete a `toDus-API`

---

## [1.3.2] - 2026-06-19

### 🔧 Corregido
- Flujo de publicación en GitHub Actions

---

## [1.3.1] - 2026-06-19

### 🎉 Agregado
- Soporte para proxy HTTP y SOCKS5

---

## [1.3.0] - 2026-06-19

### 🎉 Agregado
- ✅ Soporte completo para grupos MUC Light (`GroupClient`)
- ✅ Roles de grupo y eventos
- ✅ Auto-detección de destino privado/grupo
- ✅ Mensajes de ubicación y eventos
- ✅ Callbacks por grupo
- ✅ Modulo `stanzas/` reorganizado
- ✅ Modulo `client/` con mixins
- ✅ `pyproject.toml` moderno (PEP 621)
- ✅ Tests unitarios con pytest
- ✅ CI/CD con GitHub Actions

---

## [1.2.0] - 2026-06-01

### 🎉 Agregado
- Envío de stickers, contactos, botones interactivos
- Edición y eliminación de mensajes
- Parser incremental (`IncrementalParser`)

---

## [1.1.0] - 2026-05-15

### 🎉 Agregado
- Envío de imágenes y videos con metadata
- Subida/descarga de archivos
- Perfil de usuario (alias, bio, avatar)
- Utilidades: `format_size`, `get_image_dimensions`

---

## [1.0.0] - 2026-05-01

### 🎉 Agregado
- ✅ Cliente básico XMPP para ToDus
- ✅ Cliente stateful con auto-login
- ✅ Autenticación por SMS + JWT
- ✅ Envío/recepción de mensajes
- ✅ Excepciones personalizadas
- ✅ Constantes del protocolo
