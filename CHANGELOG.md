# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

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

[1.4.7]: https://github.com/ElJoker63/toDus-API/compare/v1.4.6...v1.4.7
[1.4.6]: https://github.com/ElJoker63/toDus-API/compare/v1.4.5...v1.4.6
[1.4.5]: https://github.com/ElJoker63/toDus-API/compare/v1.4.4...v1.4.5
[1.4.4]: https://github.com/ElJoker63/toDus-API/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/ElJoker63/toDus-API/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/ElJoker63/toDus-API/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/ElJoker63/toDus-API/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/ElJoker63/toDus-API/compare/v1.3.9...v1.4.0
[1.3.9]: https://github.com/ElJoker63/toDus-API/compare/v1.3.8...v1.3.9
[1.3.8]: https://github.com/ElJoker63/toDus-API/compare/v1.3.7...v1.3.8
[1.3.7]: https://github.com/ElJoker63/toDus-API/compare/v1.3.6...v1.3.7
[1.3.6]: https://github.com/ElJoker63/toDus-API/compare/v1.3.5...v1.3.6
[1.3.5]: https://github.com/ElJoker63/toDus-API/compare/v1.3.4...v1.3.5
[1.3.4]: https://github.com/ElJoker63/toDus-API/compare/v1.3.3...v1.3.4
[1.3.3]: https://github.com/ElJoker63/toDus-API/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/ElJoker63/toDus-API/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/ElJoker63/toDus-API/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/ElJoker63/toDus-API/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/ElJoker63/toDus-API/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/ElJoker63/toDus-API/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ElJoker63/toDus-API/releases/tag/v1.0.0
