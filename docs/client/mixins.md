# API de Mixins

Referencia completa de todos los métodos organizados por mixin.

## Autenticación

| Método | Descripción |
|--------|-------------|
| `request_code(phone_number)` | Solicita código de verificación SMS |
| `validate_code(phone_number, code) -> str` | Valida el código y retorna el token |
| `login(phone_number, password) -> str` | Inicia sesión con contraseña |

## Mensajería

| Método | Descripción |
|--------|-------------|
| `send_message(to, body, reply_to_id) -> str` | Envía texto |
| `edit_message(to, new_body, original_msg_id, reply_to_id) -> str` | Edita un mensaje |
| `send_file_message(to, url, file_type, caption, file_name, file_size, reply_to_id) -> str` | Envía archivo |
| `send_image_message(to, url, file_name, file_size, width, height, thumbnail, caption, reply_to_id) -> str` | Envía imagen con metadatos |
| `send_image_message_simple(to, url, file_name, file_size, msg_id, reply_to_id) -> str` | Envía imagen sin metadatos |
| `send_button_message(to, text, buttons, reply_to_id) -> str` | Envía mensaje con botones |
| `send_contact_message(to, contact_id, contact_name, contact_phone, reply_to_id) -> str` | Envía contacto |
| `send_sticker_message(to, sticker_id, sticker_name, sticker_pack, sticker_hash, reply_to_id) -> str` | Envía sticker |
| `send_video_message(to, url, video_id, file_name, file_size, duration, width, height, thumbnail, info_text, reply_to_id) -> str` | Envía video |
| `send_location_message(to, lat, lon, zoom, text, reply_to_id) -> str` | Envía ubicación |
| `send_event_message(to, title, start, end, all_day, ics_data, event_id, reply_to_id) -> str` | Envía evento |
| `send_chat_state(to, state)` | Notifica estado de escritura |
| `delete_message(to, message_id, msg_type, body, media_xml, reply_to_id) -> str` | Elimina mensaje |
| `send_read_receipt(to, msg_id, msg_type) -> str` | Confirma lectura |
| `listen_messages(callback)` | Bucle de escucha con reconexión |

## Archivos

| Método | Descripción |
|--------|-------------|
| `reserve_upload_url(size, file_type, file_name) -> tuple` | Reserva URLs de subida/descarga |
| `get_real_download_url(url) -> str` | Obtiene URL real de descarga |
| `upload_file(data, file_type, progress_callback, file_name) -> str` | Sube archivo y retorna URL |
| `download_file(url, path) -> int` | Descarga a ruta local |
| `download_file_to_folder(url, folder, filename) -> tuple` | Descarga a carpeta |

## Perfil

| Método | Descripción |
|--------|-------------|
| `update_profile(alias, bio, picture_url, thumbnail_url) -> bool` | Actualiza perfil |
| `upload_avatar(image_data, thumbnail_data) -> tuple` | Sube avatar |
| `set_todus_id(new_id, msg_id) -> str` | Cambia @username |

## Canales

| Método | Descripción |
|--------|-------------|
| `create_channel(name, link, public, desc, picture, subs) -> str` | Crea canal |
| `publish_to_channel(channel_jid, publ_xml) -> str` | Publica en canal |
| `subscribe_channel(channel_jid) -> str` | Se suscribe |
| `leave_channel(channel_jid) -> str` | Abandona canal |
| `get_my_channels() -> str` | Lista canales del usuario |
| `get_channel_info(channel_link) -> str` | Info del canal |
| `get_channel_publications(channel_jid, last_id, limit) -> str` | Publicaciones |

## Estados

| Método | Descripción |
|--------|-------------|
| `publish_status(json_content) -> str` | Publica estado |
| `delete_status(status_id) -> str` | Elimina estado |
| `get_status(status_id) -> str` | Obtiene estado |
| `follow_user(phone_number) -> str` | Sigue estados |
| `unfollow_user(phone_number) -> str` | Deja de seguir |
| `get_followers(phone_number, limit) -> str` | Lista seguidores |
| `get_following(phone_number, limit) -> str` | Lista seguidos |
| `get_follower_info(phone_number) -> str` | Info de relación |

## Privacidad

| Método | Descripción |
|--------|-------------|
| `get_profile_privacy() -> str` | Privacidad de perfil |
| `set_profile_privacy(profile_photo, last, info) -> str` | Configura privacidad |
| `get_group_privacy() -> str` | Privacidad de grupos |
| `set_group_privacy(who_can, exceptions) -> str` | Privacidad de grupos |

## Bloqueos

| Método | Descripción |
|--------|-------------|
| `block_user(phone_number) -> str` | Bloquea usuario |
| `unblock_user(phone_number) -> str` | Desbloquea |
| `get_block_list() -> str` | Lista bloqueados |
| `get_block_list_paginated(limit, offset) -> str` | Lista paginada |

## Última conexión

| Método | Descripción |
|--------|-------------|
| `get_last_seen(phone_number) -> str` | Última conexión |

## Ubicación

| Método | Descripción |
|--------|-------------|
| `set_location(lat, lon) -> str` | Comparte ubicación |
| `hide_location() -> str` | Oculta ubicación |
| `get_people_near(limit, offset) -> str` | Personas cerca |
| `get_near_status() -> str` | Estado de visibilidad |

## Llamadas

| Método | Descripción |
|--------|-------------|
| `get_turn_credentials(phone_number) -> str` | Credenciales TURN |
| `start_call(phone_number, content) -> str` | Inicia llamada |
| `end_call(phone_number, reason) -> str` | Finaliza llamada |
| `pickup_call(phone_number, content) -> str` | Responde llamada |
| `reject_call(phone_number) -> str` | Rechaza llamada |
