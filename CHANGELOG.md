# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [1.9.1] - 2026-09-06

### Fixed
- **CRÍTICO #1 — `stop_event` contaminado por `_listen_loop` finally**:
  El bug que apagaba bots que pasaban su propio `stop_event` a
  `listen_messages`. El `finally` de `_listen_loop` hacía `stop_event.set()`
  para detener el keepalive worker — pero como recibía el mismo event que
  el caller, lo dejaba seteado para siempre. Tras cualquier fallo de red,
  el caller creía que el usuario había pedido parar. Ahora el keepalive
  usa un event interno separado y el `stop_event` del caller se respeta.
- **#2 — `IncrementalParser` reemitía stanzas en feeds separados**:
  El `seen_ids` era local a cada `feed()`, así que el mismo `id` en dos
  feeds distintas se emitía dos veces. Ahora el set persiste en
  `self._seen_ids` entre llamadas (con límite de 50000 IDs).
- **#3 — `IncrementalParser` no descartaba `<stream:stream>` inicial**:
  El header `<?xml...?><stream:stream...>` se quedaba pegado al buffer
  indefinidamente (el cleanup solo disparaba si buffer > 20000). Ahora
  se descarta de forma determinista al inicio de cada `feed()`.
- **#4 — `IncrementalParser` no parseaba `<m .../>` self-closing**:
  El patrón exigía `</m>` explícito. Ahora hay un patrón adicional para
  stanzas self-closing (y un caso límite para `<m ...>` sin `/>` ni `</m>`).
- **#5 — `parse_todus_message` no respetaba CDATA en `<b>`**:
  El body quedaba corrupto como `"<![CDATA[hello <world>]]>"` en vez de
  `"hello <world>"`. Ahora se limpia el CDATA antes de `unescape_xml`.
- **#6 — `parse_todus_message` no manejaba `<b>` anidados**:
  El regex non-greedy cortaba en el primer `</b>`, perdiendo el contenido
  después del anidado. Ahora `_match_balanced_tag` cuenta niveles para
  emparejar el `</b>` de cierre correcto.
- **#7 — `RateLimiter.wait()` race condition**:
  Dos threads podían ambos leer el mismo `sleep_time`, dormir, y ambos
  hacer `append` sin verificar. El limiter terminaba con más timestamps
  que `max_ops`. Ahora el cálculo + sleep + append es atómico con
  `threading.Condition`.
- **#8 — `send_chat_state` no usaba rate limiter**:
  Podía saturar el servidor si el cliente envía `composing` por cada
  keystroke. Ahora usa `self._rate_limiter.wait()` como los demás `send_*`.
- **#9 — `send_call_signal` no usaba rate limiter**: mismo fix que #8.
- **#10 — `upload_file` timeout 60s hardcoded**:
  Insuficiente para archivos grandes (1GB) en conexiones cubanas lentas.
  Ahora el parámetro `timeout` es configurable (default 300s = 5 min).
- **#11 — `download_file` no validaba integridad de `.part`**:
  Si un `.part` previo era corrupto o pertenecía a otro archivo, se
  concatenaba y el resultado quedaba corrupto. Ahora se hace un HEAD
  pre-resume para validar tamaño; si el `.part` es más grande que el
  total, se descarta.
- **#12 — `_handshake` sin timeout total (loop infinito potencial)**:
  Si el servidor enviaba algo que el state machine no reconocía, el
  `while True` seguía para siempre. Ahora limita el tiempo total a
  30s y aborta si el estado no avanza tras 3 recv consecutivos.
- **#13 — `get_real_download_url` retornaba `""` silenciosamente**:
  Si la respuesta tenía `i='sid-2'` y `du=` pero el regex no capturaba,
  retornaba `""`. El caller usaba `""` como URL y el error HTTP era
  críptico. Ahora levanta `ConnectionLostError` con un mensaje claro.
- **#14 — `upload_file` override rompía LSP**:
  El override en `ToDusClient2` no aceptaba `token`, así que una
  subclase que llamara `super().upload_file(token, data, ...)` se
  rompía. Ahora acepta `token` opcional (default `self._token`).
- **#15 — `_is_group_target` trataba números no-cubanos como grupos**:
  Heurística histórica documentada pero peligrosa: un número como
  `5511912345678` (Brasil) se trataba como grupo. Se mantiene la
  heurística para no romper compatibilidad, pero se documenta el
  peligro en el docstring.

### Added
- `tests/test_fixes_v1_9_1.py`: 17 tests nuevos, uno por bug arreglado.
  Cada test falla en v1.9.0 y pasa en v1.9.1.
- `_match_balanced_tag(stanza, tag)` en `todus/parser.py`: helper
  público para emparejar tags XML balanceados con anidamiento.

### Changed
- `RateLimiter` ahora usa `threading.Condition` internamente (además del
  lock). La API pública (`wait`, `try_acquire`, `available`, `reset`) no
  cambia.
- `IncrementalParser.reset()` ahora también limpia `self._seen_ids`.

## [1.9.0] - 2026-08-30

### Added
- **`login_with_phone_only()`**: nuevo método oficial de autenticación que
  solo requiere el número de teléfono (sin password, SMS ni JWT previo).
  Explota una debilidad del endpoint `/v2/auth/token` que acepta cualquier
  UUID (con guiones removidos, primeros 32 chars) como "password" sin
  validar contra el password real de la cuenta.
  - API pública: `ToDusClient2.login_with_phone_only()` y
    `ToDusAuthMixin.login_with_phone_only(phone) -> str`
  - UUID hardcodeado: `fake-1234-5678-90ab-cdef12345678`
  - Headers exactos: `content-type: application/octet-stream` +
    `user-agent: ToDus 2.1.1`
  - Payload protobuf: `sf(1, PHONE) + sf(2, SECRET)`
  - JWT extraído del body con regex `eyJ...`
  - Documentación actualizada en `docs/authentication.md` con los 4 métodos
    de login (contraseña, SMS, JWT previo, solo-con-número).
- **`ToDusClient2.send_message()`** ahora acepta parámetro opcional
  `msg_id` para que la cola persistente y el envío XMPP usen el mismo ID
  (los receipts casen correctamente).
- **`MessageStore.reset_retry_count()`**: resetea el contador de reintentos
  tras un reenvío exitoso.
- **`MessageStore.clear_stale()`**: limpia mensajes PENDING/FAILED antiguos
  para evitar acumulación infinita de mensajes atascados.
- **`MessageStore.close()`** y soporte de context manager (`with`).
- **`ToDusClientWithQueue.close()`** y soporte de context manager.
- **`UserWarning`** visible cuando `verify_ssl=False` (antes era silencioso).

### Fixed
- **P0 #1 — Loop infinito en retry worker**: `_retry_worker_loop` marcaba
  el mensaje como `PENDING` (en vez de `SENT`) tras un reenvío exitoso,
  causando que el worker reprocesara el mismo mensaje infinitamente.
  Ahora marca como `SENT` y resetea `retry_count`.
- **P0 #2 — `send_message_queued` perdía mensajes en fallo**: si
  `super().send_message()` lanzaba una excepción, el mensaje nunca se
  encolaba y se perdía sin posibilidad de retry. Ahora encola ANTES de
  enviar y maneja errores de red (PENDING para retry) vs auth (FAILED
  permanente) de forma diferenciada.
- **flake8 CI**: 4 violaciones que rompían el workflow de CI corregidas:
  - `todus/cache/store.py:9` — `dataclasses.field` importado pero no usado
  - `todus/client/base.py:9` — `urllib3` importado pero no usado en top-level
  - `todus/client/base.py:78` — redefinición de `urllib3`
  - `todus/client_with_queue.py:5` — `todus.util` importado pero no usado
  - Resultado: `flake8 todus/ --max-line-length=120 --count` → **0**
- **`escape_xml`** ahora también escapa comillas dobles (`"`) de forma
  defensiva.
- **`generate_msg_id`** usa `secrets.token_hex(16)` en vez de MD5 de token
  aleatorio.
- **`request_code`/`validate_code`/`login`** envuelven `requests.RequestException`
  en `AuthenticationError` (antes propagaban `HTTPError` sin jerarquía).
- **`MessageQueue.mark_failed`** ahora distingue retry agendado (`True`)
  de `FAILED` permanente (`False`). Antes ambos retornaban `True`.
- **`MessageStore.add`** usa `INSERT OR IGNORE` (no sobrescribe
  silenciosamente mensajes existentes con mismo `msg_id`).
- **`get_real_download_url`** usa regex no greedy para no capturar de más.
- **`download_file_to_folder`** elimina el `HEAD` innecesario (la URL corta
  siempre requiere resolución XMPP previa).
- **`Message.created_at`** anotado correctamente como `Optional[float]`.

### Changed
- **`normalize_phone()`** simplificado a **Cuba-only**: ToDus es una
  plataforma cubana y los SMS solo se envían a números cubanos. Se elimina
  el parámetro `country_code` y la lógica E.164 internacional. Solo acepta
  `53XXXXXXXX` (10 dígitos) o `XXXXXXXX` (8 dígitos nacionales que se
  normalizan a 10). Números no cubanos (5511..., 1..., 34...) se rechazan.
- **`verify_ssl`** ahora es `True` por defecto (antes `False`). Se emite
  `UserWarning` si se desactiva explícitamente.
- **`_is_group_target`** solo considera teléfono válido un número cubano
  (10 dígitos empezando en 53). Cualquier otro string numérico se trata
  como `group_id`.
- **`_seen_msg_ids`** ahora usa `OrderedDict` con LRU determinista
  (`move_to_end` al re-ver, `popitem(last=False)` para podar). Antes era
  un `set` con poda no determinista.
- **`MessageStore`** usa conexión SQLite persistente compartida entre
  hilos (`check_same_thread=False` + `RLock` externo) en lugar de abrir
  una conexión nueva por operación. Activa WAL mode y `synchronous=NORMAL`.
- **`ToDusClientWithQueue.__del__`** simplificado a delegar en `close()`.

### Tests
- **+38 tests nuevos** en `tests/test_fixes.py` (total: 260 tests pasando).
  - 13 tests validan `login_with_phone_only` (UUID, SECRET, varint, sf,
    payload, headers, endpoint, extracción JWT, manejo de errores).
  - 25 tests validan los bugs P0-P2 corregidos (cola, target detection,
    LRU, context manager, SQLite persistente, mark_failed, auth errors).

---

## [1.8.0] - 2026-08-27

Alineación completa con el protocolo de la app oficial v2.1.2.
El flujo de login con
número + contraseña/token NO se modificó.

### Fixed (críticos, según análisis del protocolo)
- **Puerto XMPP**: `5222` → `1756` (puerto de producción). Añadido
  `XMPP_PORT_PROD2 = 5443` y parámetro `xmpp_port` en el constructor del
  cliente para usar puertos alternativos.
- **Chat states invertidos**: `csc` = composing y `csp` = paused
  Antes estaba al revés en envío y recepción.
- **Receipts invertidos**: `rd` = recibido/entregado (received) y
  `dd` = leído (displayed). `receipt()` ahora emite `<rd>` y
  `read_receipt()` emite `<dd>`; el parser se actualizó en consecuencia.
- **`tdack` no existe en el protocolo**: `ack()` ahora emite `<ak>`
  (elemento ACK del protocolo). El parser reconoce `<ak>` (y `<tdack>` legado).
- **Extensión `reply:n` inventada**: las respuestas usan `resend:n`
  (attrs `i`, `mi`, `uowner`). `reply_to_id` de la API
  pública se mantiene y emite `<resend>`.
- **Escrituras parciales de socket**: todos los `sock.send()` migrados a
  `sendall()` (56 sitios). Nuevo `ThreadSafeSocket` con lock por conexión
  que evita corrupción TLS entre el hilo keepalive y el loop principal.
- **Bucle infinito en `download_file()`** cuando el servidor no envía
  `Content-Length`.
- **`get_image_dimensions()` PNG**: el bucle saltaba de 8 en 8 bytes y nunca
  encontraba `IHDR` (offset fijo 12). Ahora lee el header correctamente.
- **`normalize_phone()`**: rechaza números inválidos (antes truncaba
  silenciosamente basura de 16+ dígitos) y soporta `country_code`
  internacional.
- **Keepalive**: 25s → 30s (intervalo del cliente oficial).
  Ahora usa `stop_event.wait()` para responder al stop de inmediato.
- **`ToDusClientWithQueue.__del__`**: protegido contra `AttributeError`
  cuando `__init__` falló a medias.

### Changed
- **MAM estándar XEP-0313**: namespace `todus:mam` → `urn:xmpp:mam:1` con
  formulario `jabber:x:data` (filtros `with`/`start`/`end`) y RSM.
- **Bind con resource**: `<re>md5(username)_Android</re>` como el cliente oficial.
- **Subida de archivos**: `Content-Type: application/octet-stream` en el PUT.
- **Descargas**: sin cabecera `Authorization` para URLs `/official/`,
  `/catalog/`, `/status/`, `/stream/`.
- **Botones**: atributos `btn_d` (descripción) añadidos; `btn_color` y
  `btn_row` eliminados (no existen en el protocolo). `ButtonCommand` ahora usa
  `cmd_open_web`, `cmd_copy_to_clipboard`, `cmd_add_shortcut`,
  `cmd_open_app_screen`. `ButtonSize.MID = 0.4` (antes `HALF = 0.5`,
  valor inexistente; `HALF` queda como alias deprecado de 0.4).
- **msg_id estandarizado**: todos los métodos de envío usan IDs hex de 32
  chars (`util.generate_msg_id()`), como el cliente oficial.
- **Rate limiter en todos los envíos**: antes solo `send_message()`; ahora
  también imágenes, videos, stickers, notas de voz, GIFs, reacciones,
  ediciones y borrados (protege contra bans por spam).
- **Mutación de miembros de grupo**: usa `td:g:add_occupant` con atributo
  `new_occupants` en vez del namespace `x11` (que en el protocolo es solo
  consulta).
- **CI**: el workflow de tests ya no hace commit del reporte al repo
  (contaminaba el historial); el reporte queda como artifact. Añadido paso
  de lint (flake8) al CI.
- **Lint**: flake8 de 396 violaciones → 0.
- **pyproject.toml**: URLs corregidas de toDus-API → toDus-SDK.

### Added
- **Stanzas nuevas**: `voice_message` (voice:n, con forma de onda
  `ws`), `gif_message` (gif:n), `stream_video_message` (streamvideo:n),
  `reaction_message` (reaction:n), `forward_message` (resend:n),
  `tcall_message` (tcall:n) y `mention_extension` (mention:n).
- **Métodos nuevos en `ToDusClient2`**: `send_voice_message`,
  `send_gif_message`, `send_reaction`, `forward_message`,
  `send_stream_video_message`, `send_call_signal`,
  `send_delivery_receipt` — todos con auto-detección privado/grupo.
- **IQs de grupo nuevas**: crear grupo (`x16`), mis grupos paginado
  (`todus:muclight:my_mucs:2`), promover/degradar admin
  (`td:g:promote` / `td:g:demote`), info por link (`td:g:info_by_link`) e
  info por id (`td:g:info_by_id`).
- **Métodos nuevos en `GroupClient`**: `create_group`, `get_my_groups`,
  `promote_admin`, `demote_admin`, `get_group_info_by_link`,
  `get_group_info_by_id`, `send_voice`, `send_gif`, `send_reaction`.
- **Parser**: soporte de recepción para voice, gif, streamvideo, reaction,
  mentions (lista), resend (forward/reply) y tcall; evento `ack` en el
  `EventBus`.
- **`ThreadSafeSocket`** exportado desde `todus.client.base`.
- **55 tests nuevos** (`tests/test_protocol_alignment.py`) incluyendo tests de
  escrituras concurrentes atómicas sobre socket real.

### Notas
- Las IQs `x16` (crear grupo), `td:g:promote/demote` e `info_by_link/id`
  se implementaron según el análisis del protocolo; se recomienda
  verificar contra tráfico real (MITM) antes de producción.
- Compresión de stream zlib y cert-pinning quedan pendientes (requieren
  los parámetros de negociación y los certificados del servidor).
- **MAM verificado empíricamente contra producción (2026-08-27)**: el
  servidor `im.todus.cu` responde `<error t='cancel'><service-unavailable/>`
  con el texto *"No module is handling this query"* tanto para
  `urn:xmpp:mam:1` como para el legado `todus:mam` — es decir, ejabberd
  no tiene `mod_mam` cargado y el historial NO está disponible en
  producción (el formato viejo de la v1.7.0 tampoco funcionaba: enviaba
  la query y cerraba la sesión sin leer la respuesta). Se mantiene el
  formato estándar XEP-0313 por coincidir con el protocolo oficial.
- **Test de integración real (2026-08-27)**, cuenta de producción contra
  `auth.todus.cu` / `im.todus.cu:1756` / `s3.todus.cu`: login por
  número+contraseña, handshake SASL+bind (resource `md5(usuario)_Android`
  aceptado por el servidor), mensaje de texto, respuesta `resend:n`,
  reacción `reaction:n`, edición, receipts `rd`/`dd`, chat states
  `csc`/`csp`, subida de imagen PNG con dimensiones IHDR correctas,
  borrado de mensaje y listener con keepalive concurrente durante 40s
  sin desconexiones: **todo verificado OK**.

---

## [1.7.0] - 2026-08-26

### Fixed
- **Violación LSP en `upload_file()`**: `ToDusClient2.upload_file()` ahora implementa la lógica de subida directamente en vez de llamar a `super().upload_file()`, que internamente resolvía `self.reserve_upload_url(token, ...)` al override `ToDusClient2.reserve_upload_url(size, file_type, ...)` causando `TypeError: multiple values for argument 'file_name'`.
- **`ratelimit.wait()` UnboundLocalError**: Inicializado `sleep_time = 0.0` antes del lock para evitar el error cuando el rate limit no se alcanza.
- **Redelivery de mensajes de ToDus**: `handle_parsed_stanza()` ahora deduplica mensajes por `msg_id` usando el set `_seen_msg_ids` (auto-trim a 10 000 entradas). Previene respuestas repetidas al reconectar.

### Changed
- **26 métodos de 6 mixins migrados a `send_stanza + jid`**: Los mixins `Status`, `Privacy`, `Block`, `Location`, `Call` y `Last` ahora usan `self.send_stanza(stanza_xml)` y `self.jid` en vez de requerir `token` y `_xmpp_session()` directamente. Esto los hace compatibles con `ToDusClient2` sin necesidad de pasar el token manualmente.
- **Logo del proyecto** añadido a la documentación (MkDocs) y al README.

### Added
- **Workflow de releases**: Nuevo workflow `.github/workflows/release.yml` que crea automáticamente un GitHub Release extrayendo el texto de la versión correspondiente del `CHANGELOG.md`.
- Imagen `docs/assets/logo.png` (logo del proyecto).

---

## [1.6.0] - 2026-08-20

### Changed
- Bloques de código en la documentación ahora usan fondo claro en modo claro, corrigiendo el problema donde se veían oscuros.
- Enlaces del README y documentación actualizados al repositorio nyxthor-dev/toDus-API.
- Créditos del README actualizados: nyxthor-dev como mantenedor actual.

### Added
- **Rate Limiter**: Nuevo módulo `todus/ratelimit.py` con `RateLimiter` para control de tasa de peticiones.
- `RateLimiter` exportado en `todus/__init__`.

---

## [1.5.4] - 2026-06-26

### Added
- **Event Bus y Sistema de Filtros Avanzados**: Nuevo módulo `todus/events/` con dispatcher centralizado de eventos. Incluye:
  - `EventBus`: Gestor de eventos thread-safe con prioridades y propagation control.
  - `Filter` + `build_filter`: Filtros declarativos por `from_phone`, `contains_keyword`, `msg_type`, `is_group`, `group_id`, `regex` y `custom`.
  - Decorador `@client.events.on(event_type, **filters)` para registrar handlers limpiamente.
  - Soporte para handlers wildcard (`'*'`) que capturan todos los eventos.
  - Despacho automático de 7 tipos de eventos: `message`, `presence`, `receipt`, `iq`, `tdack`, `deleted`, `chat_state`.
  - Método `handle_parsed_stanza(msg, *, sock, callback)` para manejar stanzas parseadas.
- **Documentación de Event Bus**: Nueva sección `docs/events/overview.md` con guía completa y ejemplos.

### Changed
- **Integración de EventBus en cliente**: `ToDusClient` ahora inicializa `self.events = EventBus()` automáticamente.
- **Mejora en `_listen_loop`**: Refactorizada para usar `handle_parsed_stanza` y despachar eventos a `EventBus`.
- **Actualización de mkdocs.yml**: Agregada sección "🎯 Event Bus y Filtros" en navegación.
- **Ejemplos avanzados**: Nuevo ejemplo de "Bot Reactivo con EventBus" en `examples_advanced.md`.

### Fixed
- **Thread-safety en dispatch**: EventBus usa `RLock` para operaciones thread-safe.
- **Manejo robusto de excepciones**: Si un filtro o handler falla, se registra pero no rompe la propagación.

### Tests Added
- `tests/test_events.py`: 5 tests para filtros, prioridades, wildcard y unsubscribe.
- `tests/test_client_events.py`: Integración de eventos en cliente (7 tipos de eventos).

---

## [1.5.3] - 2026-06-21

### Added
- **Message Queue System**: Nuevo módulo `todus/cache/` con almacenamiento persistente de mensajes en SQLite. Incluye:
  - `MessageStore`: CRUD thread-safe para mensajes con índices optimizados (status, "to", created_at).
  - `MessageQueue`: Sistema de cola con reintentos automáticos, callbacks de eventos y backoff exponencial con jitter.
  - `MessageQueueMixin`: Mixin composable para integrar queue en cualquier cliente.
  - `ToDusClientWithQueue`: Cliente completo con soporte de queue integrado.
- **Documentación HTML**: Nueva documentación visual en `documentacion.html` con diseño blanco/rojo, ejemplos terminales Linux/Mac, navegación interactiva y secciones detalladas (Introducción, Inicio Rápido, Instalación, Ejemplos, Características, Mensajería, Message Queue).
- **Estados de Mensaje**: Implementación completa del ciclo de vida del mensaje (pending → sent → delivered → read/failed).
- **Callbacks de Evento**: Registro de funciones callback para eventos de mensajes: `on_message_sent`, `on_message_delivered`, `on_message_read`, `on_message_failed`.
- **Estadísticas de Queue**: Método `get_queue_stats()` para monitoreo en tiempo real de mensajes por estado.

### Changed
- **Optimización del cliente `ToDusClient2`**: Refactorización elimando ~200 líneas de código duplicado en métodos de envío.
- **Mejora en `listen_messages`**: Ahora soporta `max_retries` configurable (default 10) con exponential backoff mejorado y mejor logging de errores.
- **Esquema de persistencia**: Almacenamiento de metadata JSON para campos personalizados en el sistema de queue.
- **Exports actualizados**: Nuevo `__all__` en `todus/__init__.py` incluyendo `MessageStore`, `Message`, `MessageStatus`, `MessageQueue`, `ToDusClientWithQueue`.

### Fixed
- **Bug en SQL reserved word**: Corrección del error "sqlite3.OperationalError: near 'to': syntax error" escapando la columna `"to"` en CREATE TABLE e INSERT statements con parámetros posicionales.
- **Thread-safety mejorada**: Implementación de RLock en todas las operaciones de base de datos del MessageStore para evitar condiciones de carrera.
- **Limpieza de recursos**: Método `__del__` en `ToDusClientWithQueue` para parar correctamente el worker thread de reintentos.
- **Eliminación de mensajes antiguos**: Implementación de `clear_old_messages()` para limpiar mensajes con más de 30 días automáticamente.

## [1.5.2] - 2026-06-20

### Added
- **Sistema de Mensajes Programados (Scheduler)**: Nueva funcionalidad para programar el envío de mensajes automáticos.
  - `send_later(to, body, delay)`: Envía un mensaje después de un tiempo determinado (ej. 5 minutos).
  - `schedule_daily(to, body, hour, minute)`: Envía un mensaje todos los días a una hora específica.
  - `schedule_interval(to, body, interval)`: Envía un mensaje cada cierto intervalo de tiempo (ej. cada hora).
  - `cancel_task(task_id)`: Cancela una tarea programada.
  - `list_tasks()`: Lista todas las tareas programadas.
  - `get_scheduler_stats()`: Obtiene estadísticas del scheduler (tareas pendientes, próxima ejecución, etc.).
  - `stop_scheduler()`: Detiene el scheduler y libera el hilo.
- **Verificación SSL configurable**: Nuevo parámetro `verify_ssl` en `ToDusClientBase` y `ToDusClient2` para activar/desactivar la verificación de certificados SSL. Por defecto `False` para mantener compatibilidad con versiones anteriores.
- **Backoff exponencial con jitter**: Mejora en el método `listen_messages` para reconexiones inteligentes. Ahora los reintentos aumentan progresivamente (1s, 2s, 4s, 8s, 16s, 32s, máximo 60s) con un factor aleatorio del 0-30% para evitar el "efecto rebaño".

### Changed
- **Refactorización de `ToDusClient2`**: Eliminada la duplicación de código en los métodos de envío (`send_message`, `send_file_message`, `send_image_message`, etc.) mediante el nuevo método interno `_send_to_target`. Centraliza la lógica de detección de grupos y autenticación.
- **Seguridad SSL mejorada**: Ahora se puede activar la verificación de certificados en conexiones HTTP y XMPP, eliminando la dependencia de la desactivación forzosa de seguridad.

### Fixed
- **Reconexiones más eficientes**: Reemplazado el `time.sleep(15)` fijo por un sistema de backoff exponencial que reduce la carga del servidor en caídas prolongadas y acelera la reconexión en fallos leves.
- **Eliminación de duplicación de código**: Los métodos de envío ahora son más mantenibles y fáciles de extender.

## [1.5.1] - 2024-06-20

### Fixed
- Corrección de la rama de la documentación.

## [1.5.0] - 2024-06-20

### Added
- **Cobertura 100% de la API de ToDus:** Implementación de todas las funcionalidades internas restantes.
- **Privacidad (`ToDusPrivacyMixin`)**: Métodos para configurar y consultar quién ve tu perfil o te añade a grupos (`get_profile_privacy`, `set_profile_privacy`, `get_group_privacy`, `set_group_privacy`).
- **Bloqueos (`ToDusBlockMixin`)**: Gestión de lista negra de contactos (`block_user`, `unblock_user`, `get_block_list`, `get_block_list_paginated`).
- **Última Conexión (`ToDusLastMixin`)**: Consulta de actividad reciente de usuarios (`get_last_seen`).
- **Ubicación (`ToDusLocationMixin`)**: Geolocalización y Personas Cerca (`set_location`, `hide_location`, `get_people_near`, `get_near_status`).
- **Llamadas (`ToDusCallMixin`)**: Señalización XMPP para VoIP (`start_call`, `pickup_call`, `reject_call`, `end_call`, `get_turn_credentials`).

## [1.4.7] - 2026-06-20

### Added
- Implementación base de **Estados / Historias de ToDus** (`StatusManager`). Se añadió el mixin `ToDusStatusMixin` y soporte nativo XMPP (`td:status:*`):
  - `publish_status`: Publica historias mediante carga Base64 automática de payloads.
  - `delete_status`: Permite eliminar un estado publicado.
  - `get_status`: Recupera un estado de otro usuario.
  - `follow_user` y `unfollow_user`: Suscripción y cancelación de estados de otros usuarios.
  - `get_followers`, `get_following` y `get_follower_info`: Interfaz completa para consultar la red de seguidores y seguir de manera paginada.

## [1.4.6] - 2026-06-20

### Added
- Implementación base completa de **Canales de ToDus**. Se incluyó el mixin `ToDusChannelMixin` con funciones nativas XMPP (`todus:ch:*`) para gestionar canales:
  - `create_channel`: Permite crear nuevos canales.
  - `get_my_channels`: Lista los canales del usuario.
  - `get_channel_info`: Obtiene la información del canal por su enlace.
  - `publish_to_channel`: Publica mensajes XML nativos en canales.
  - `get_channel_publications`: Obtiene los últimos mensajes (paginación de historial).
  - `subscribe_channel` y `leave_channel`: Gestión de membresía de canal.
- El parser interno `parse_iq` ahora intercepta nativamente los elementos `<query>` que devuelven información compleja (como historiales y propiedades de canales) para su fácil extracción.

### Fixed
- Solucionado el problema en la actualización del perfil (nombre/alias se convertía en `~`). Ahora se aconseja empaquetar en una misma llamada a `update_profile` todos los atributos que se desean mantener. Se agregó el parámetro opcional `thumbnail_url` faltante en los ejemplos.

## [1.4.5] - 2026-06-20

### Fixed
- Corregido un test automatizado (`test_upload_avatar_uses_session`) que estaba fallando y bloqueando el despliegue a PyPI debido al cambio previo en la firma de `reserve_upload_url`.

## [1.4.4] - 2026-06-20

### Fixed
- Corregido un `TypeError` interno en la función `upload_avatar` provocado por la sobreescritura de parámetros en el manejo de firmas mixtas (`reserve_upload_url`).

## [1.4.3] - 2026-06-20

### Added
- Añadido el método `set_todus_id` al `ToDusProfileMixin` para permitir cambiar el `@username` del usuario mediante la API XMPP nativa de ToDus (utilizando el stanza `todus:users:updatetodusid`).

## [1.4.2] - 2026-06-20

### Changed
- Reescrito el método `update_profile` del `ToDusProfileMixin` para funcionar con la API REST actual. Ahora utiliza payloads construidos manualmente en Protobuf hacia el endpoint `v2/todus/users.me` en lugar de JSON, reparando finalmente la funcionalidad de actualizar perfil (nombre, biografía y foto).
- Se modificó la inyección del token JWT en el cliente de perfiles para ajustarse al estándar esperado por `auth.todus.cu` (sin el prefijo `Bearer`).

## [1.4.1] - 2026-06-20

### Added
- Integración nativa de namespaces `x11`, `x13`, `x14` para gestión avanzada de grupos.
- Implementado el método correcto de `leave()` mediante petición IQ `x13`.
- Nuevas funciones de miembros: `get_members`, `set_member_role`, `kick_member`.
- Nuevas funciones de enlaces: `get_invite_link`, `revoke_invite_link`.
- Funciones parseadoras auxiliares: `parse_members_response`, `parse_invite_link_response`.
- Ejemplo funcional `examples/send_grupo_admin.py`.

## [1.4.0] - 2026-06-20

### Added
- Implementadas funciones para la administración de grupos MUC Light.
- Nuevos métodos en `GroupClient` para actualizar la información de un grupo:
  - `set_name`: Permite cambiar el nombre del grupo (`<g4>`).
  - `set_subject`: Permite cambiar la descripción o asunto del grupo (`<subject>`).
  - `set_avatar`: Permite actualizar el avatar (imagen) del grupo (`<g3>` y `<picture_thumbnail_url>`).

## [1.3.9] - 2026-06-20

### Fixed
- Corregida la generación de stanzas salientes (tanto en mensajes de grupo `group.py` como `private.py`), cambiando el atributo `o='{to}'` por el correcto `to='{to}'`. Esto resuelve problemas donde los mensajes no se enrutaban o no se mostraban correctamente al enviar contenidos a los grupos.
- Añadido el atributo faltante `xmlns='jc'` en `video_message` de los chats privados.

## [1.3.8] - 2026-06-20

### Fixed
- Corregido un bug en los stanzas de grupos (`group_file_message`, `group_image_message`, `group_video_message`) donde el parámetro `caption` era ignorado y no se incluía en el XML. Ahora los grupos soportan correctamente pies de foto y descripciones.

### Changed
- Actualizados los parámetros de autenticación a `AUTH_VERSION_NAME = "2.1.2"` y `AUTH_VERSION_CODE = "30102"` para igualar la versión actual de la app oficial de ToDus.

## [1.3.7] - 2026-06-20

### Fixed
- Normalizado automáticamente el número de teléfono y eliminados espacios/saltos de línea accidentales del token/password en `ToDusClient2` y los métodos del mixin de autenticación.
- Corregida la serialización de payload protobuf en la autenticación para calcular dinámicamente el tamaño de los campos de texto en lugar de usar longitudes fijas de bytes, evitando fallos `400 Bad Request` ante caracteres extraños (como retornos de carro `\r` generados por archivos `.env` con formato CRLF en Docker).

## [1.3.6] - 2026-06-20

### Fixed
- Desactivada la verificación SSL en las peticiones HTTP y en el socket XMPP para evitar errores de validación de certificados de ToDus/Cuba en entornos de producción sin CAs locales (como contenedores Docker slim/alpine).
- Silenciadas las advertencias de `InsecureRequestWarning` producidas por la desactivación de verificación SSL en `requests`.

## [1.3.5] - 2026-06-20

### Fixed
- Corregidos y optimizados los badges del `README.md` para dar soporte a repositorios privados utilizando badges nativos de GitHub Actions y un badge estático para la licencia.

### Changed
- Migrado el flujo de publicación de PyPI en GitHub Actions a Trusted Publishing (OIDC) para evitar fallos de autenticación con tokens y simplificar el proceso.

## [1.3.4] - 2026-06-20

### Fixed
- Asegurado que las operaciones de subida de archivos (`upload_file`) y avatares (`upload_avatar`) utilicen el proxy configurado al direccionarlas a través de la sesión del cliente.
- Agregados tests unitarios para verificar el comportamiento de proxies en la subida de archivos y avatares.

## [1.3.3] - 2026-06-19

### Changed
- Renombrado el paquete a `toDus-API`.

## [1.3.2] - 2026-06-19

### Fixed
- Corregido el flujo de publicación en GitHub Actions para usar `secrets.PYPI_API_TOKEN`.

## [1.3.1] - 2026-06-19

### Added
- Soporte inicial para proxy HTTP y SOCKS5 en peticiones HTTP y sockets XMPP.

## [1.3.0] - 2026-06-19

### Added
- Soporte completo para grupos MUC Light (`GroupClient`)
- Roles de grupo (`GroupRole`) y eventos de grupo (`GroupEvent`)
- Auto-detección de destino privado/grupo en `ToDusClient2`
- Envío de mensajes de ubicación (`send_location_message`)
- Envío de mensajes de eventos/calendario (`send_event_message`)
- Callbacks específicos por grupo (`on_group_message`)
- Firma de URLs con nombre legible de archivo (`sanitize_filename`)
- Soporte de progreso en subidas (`progress_callback`)
- Módulo `stanzas/` reorganizado en subdirectorio
- Módulo `client/` reorganizado en subdirectorio con mixins
- `pyproject.toml` moderno (PEP 621)
- Tests unitarios con pytest
- CI/CD con GitHub Actions

### Changed
- Estructura interna reorganizada para claridad
- Migración de `setup.py` a `pyproject.toml`

## [1.2.0] - 2026-06-01

### Added
- Envío de stickers (`send_sticker_message`)
- Envío de contactos (`send_contact_message`)
- Envío de botones interactivos (`send_button_message`)
- Edición de mensajes (`edit_message`)
- Eliminación de mensajes (`delete_message`)
- Parser incremental de stanzas XMPP (`IncrementalParser`)

## [1.1.0] - 2026-05-15

### Added
- Envío de imágenes con dimensiones y thumbnail
- Envío de videos con metadata
- Subida y descarga de archivos con `FileType`
- Perfil de usuario (alias, bio, avatar)
- Utilidades: `format_size`, `get_image_dimensions`, `generate_blurhash`

## [1.0.0] - 2026-05-01

### Added
- Cliente básico XMPP para ToDus (`ToDusClient`)
- Cliente stateful con auto-login (`ToDusClient2`)
- Autenticación por SMS + JWT
- Envío y recepción de mensajes de texto
- Manejo de excepciones personalizadas
- Constantes del protocolo ToDus