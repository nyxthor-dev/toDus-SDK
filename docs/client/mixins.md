<!-- docs/client/mixins.md -->
<h1>Mixins – API Completa del Cliente</h1>
<p>Esta página documenta todos los mixins que componen <code>ToDusClient2</code>. Cada mixin agrupa métodos por dominio funcional.</p>

<h2>ToDusAuthMixin (Autenticación)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>request_code(phone_number)</code></td><td>Solicita código de verificación SMS.</td></tr>
        <tr><td><code>validate_code(phone_number, code) -> str</code></td><td>Valida el código y retorna el token.</td></tr>
        <tr><td><code>login(phone_number, password) -> str</code></td><td>Inicia sesión con contraseña.</td></tr>
    </tbody>
</table>

<h2>ToDusMessageMixin (Mensajería Privada)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>send_message(token, to_jid, body, reply_to_id) -> msg_id</code></td><td>Envía texto.</td></tr>
        <tr><td><code>edit_message(token, to_jid, new_body, original_msg_id, reply_to_id) -> msg_id</code></td><td>Edita un mensaje.</td></tr>
        <tr><td><code>send_file_message(token, to_jid, url, file_type, caption, file_name, file_size, reply_to_id) -> msg_id</code></td><td>Envía archivo.</td></tr>
        <tr><td><code>send_image_message(token, to_jid, url, file_name, file_size, width, height, thumbnail, caption, reply_to_id) -> msg_id</code></td><td>Envía imagen con metadatos.</td></tr>
        <tr><td><code>send_image_message_simple(token, to_jid, url, file_name, file_size, msg_id, reply_to_id) -> msg_id</code></td><td>Envía imagen sin metadatos.</td></tr>
        <tr><td><code>send_button_message(token, to_jid, text, buttons, reply_to_id) -> msg_id</code></td><td>Envía mensaje con botones.</td></tr>
        <tr><td><code>send_contact_message(token, to_jid, contact_id, contact_name, contact_phone, reply_to_id) -> msg_id</code></td><td>Envía contacto.</td></tr>
        <tr><td><code>send_sticker_message(token, to_jid, sticker_id, sticker_name, sticker_pack, sticker_hash, reply_to_id) -> msg_id</code></td><td>Envía sticker.</td></tr>
        <tr><td><code>send_video_message(token, to_jid, url, video_id, file_name, file_size, duration, width, height, thumbnail, info_text, reply_to_id) -> msg_id</code></td><td>Envía video.</td></tr>
        <tr><td><code>send_location_message(token, to_jid, lat, lon, zoom, text, reply_to_id) -> msg_id</code></td><td>Envía ubicación.</td></tr>
        <tr><td><code>send_event_message(token, to_jid, title, start, end, all_day, ics_data, event_id, reply_to_id) -> msg_id</code></td><td>Envía evento.</td></tr>
        <tr><td><code>send_chat_state(token, to_jid, state)</code></td><td>Notifica estado de escritura.</td></tr>
        <tr><td><code>delete_message(token, to_jid, message_id, msg_type, body, media_xml, reply_to_id) -> msg_id</code></td><td>Elimina mensaje.</td></tr>
        <tr><td><code>send_read_receipt(token, to_jid, msg_id, msg_type) -> msg_id</code></td><td>Confirma lectura.</td></tr>
        <tr><td><code>listen_messages(token, callback)</code></td><td>Bucle de escucha de mensajes.</td></tr>
    </tbody>
</table>

<h2>ToDusFileMixin (Archivos)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>reserve_upload_url(token, size, file_type, file_name) -> (up_url, down_url)</code></td><td>Reserva URLs de subida/descarga.</td></tr>
        <tr><td><code>get_real_download_url(token, url) -> str</code></td><td>Obtiene URL real de descarga.</td></tr>
        <tr><td><code>upload_file(token, data, file_type, progress_callback, file_name) -> str</code></td><td>Sube archivo y retorna URL.</td></tr>
        <tr><td><code>download_file(token, url, path) -> int</code></td><td>Descarga a ruta local.</td></tr>
        <tr><td><code>download_file_to_folder(token, url, folder, filename) -> (int, str)</code></td><td>Descarga a carpeta.</td></tr>
    </tbody>
</table>

<h2>ToDusProfileMixin (Perfil)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>update_profile(token, alias, bio, picture_url, thumbnail_url) -> bool</code></td><td>Actualiza perfil.</td></tr>
        <tr><td><code>upload_avatar(token, image_data, thumbnail_data) -> (profile_url, thumb_url)</code></td><td>Sube avatar.</td></tr>
        <tr><td><code>set_todus_id(new_id, msg_id) -> msg_id</code></td><td>Cambia @username (requiere sesión activa).</td></tr>
    </tbody>
</table>

<h2>ToDusChannelMixin (Canales)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>create_channel(name, link, public, desc, picture, subs) -> msg_id</code></td><td>Crea canal.</td></tr>
        <tr><td><code>publish_to_channel(channel_jid, publ_xml) -> msg_id</code></td><td>Publica en canal.</td></tr>
        <tr><td><code>subscribe_channel(channel_jid) -> msg_id</code></td><td>Se suscribe a canal.</td></tr>
        <tr><td><code>leave_channel(channel_jid) -> msg_id</code></td><td>Abandona canal.</td></tr>
        <tr><td><code>get_my_channels() -> msg_id</code></td><td>Lista canales del usuario.</td></tr>
        <tr><td><code>get_channel_info(channel_link) -> msg_id</code></td><td>Obtiene info del canal.</td></tr>
        <tr><td><code>get_channel_publications(channel_jid, last_id, limit) -> msg_id</code></td><td>Obtiene publicaciones.</td></tr>
    </tbody>
</table>

<h2>ToDusStatusMixin (Estados/Historias)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>publish_status(json_content) -> msg_id</code></td><td>Publica estado.</td></tr>
        <tr><td><code>delete_status(status_id) -> msg_id</code></td><td>Elimina estado.</td></tr>
        <tr><td><code>get_status(status_id) -> msg_id</code></td><td>Obtiene estado específico.</td></tr>
        <tr><td><code>follow_user(phone_number) -> msg_id</code></td><td>Sigue estados de usuario.</td></tr>
        <tr><td><code>unfollow_user(phone_number) -> msg_id</code></td><td>Deja de seguir.</td></tr>
        <tr><td><code>get_followers(phone_number, limit) -> msg_id</code></td><td>Lista seguidores.</td></tr>
        <tr><td><code>get_following(phone_number, limit) -> msg_id</code></td><td>Lista seguidos.</td></tr>
        <tr><td><code>get_follower_info(phone_number) -> msg_id</code></td><td>Info de relación.</td></tr>
    </tbody>
</table>

<h2>ToDusPrivacyMixin (Privacidad)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>get_profile_privacy() -> msg_id</code></td><td>Obtiene privacidad de perfil.</td></tr>
        <tr><td><code>set_profile_privacy(profile_photo, last, info) -> msg_id</code></td><td>Configura privacidad.</td></tr>
        <tr><td><code>get_group_privacy() -> msg_id</code></td><td>Obtiene privacidad de grupos.</td></tr>
        <tr><td><code>set_group_privacy(who_can, exceptions) -> msg_id</code></td><td>Configura privacidad de grupos.</td></tr>
    </tbody>
</table>

<h2>ToDusBlockMixin (Bloqueos)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>block_user(phone_number) -> msg_id</code></td><td>Bloquea usuario.</td></tr>
        <tr><td><code>unblock_user(phone_number) -> msg_id</code></td><td>Desbloquea usuario.</td></tr>
        <tr><td><code>get_block_list() -> msg_id</code></td><td>Lista bloqueados.</td></tr>
        <tr><td><code>get_block_list_paginated(limit, offset) -> msg_id</code></td><td>Lista paginada.</td></tr>
    </tbody>
</table>

<h2>ToDusLastMixin (Última Conexión)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>get_last_seen(phone_number) -> msg_id</code></td><td>Obtiene última conexión.</td></tr>
    </tbody>
</table>

<h2>ToDusLocationMixin (Ubicación)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>set_location(lat, lon) -> msg_id</code></td><td>Comparte ubicación.</td></tr>
        <tr><td><code>hide_location() -> msg_id</code></td><td>Oculta ubicación.</td></tr>
        <tr><td><code>get_people_near(limit, offset) -> msg_id</code></td><td>Personas cerca.</td></tr>
        <tr><td><code>get_near_status() -> msg_id</code></td><td>Estado de visibilidad.</td></tr>
    </tbody>
</table>

<h2>ToDusCallMixin (Llamadas)</h2>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>get_turn_credentials(phone_number) -> msg_id</code></td><td>Obtiene credenciales TURN.</td></tr>
        <tr><td><code>start_call(phone_number, content) -> msg_id</code></td><td>Inicia llamada.</td></tr>
        <tr><td><code>end_call(phone_number, reason) -> msg_id</code></td><td>Finaliza llamada.</td></tr>
        <tr><td><code>pickup_call(phone_number, content) -> msg_id</code></td><td>Responde llamada.</td></tr>
        <tr><td><code>reject_call(phone_number) -> msg_id</code></td><td>Rechaza llamada.</td></tr>
    </tbody>
</table>