<!-- docs/stanzas/overview.md -->
<h1>Stanzas – Generadores de XML</h1>
<p>El módulo <code>stanzas</code> contiene generadores de XML para todas las interacciones con el servidor XMPP de ToDus. Estos generadores son utilizados internamente por los mixins del cliente, pero también pueden ser usados directamente para personalizar comportamientos.</p>

<h2>Estructura del Módulo</h2>
<pre><code>stanzas/
├── private.py      # Mensajes privados (texto, archivos, etc.)
├── group.py        # Mensajes de grupo
├── presence.py     # Presencia (online, offline, MUC)
├── utils.py        # Utilidades XMPP (IQ, ping, auth, MAM, upload)
├── channels.py     # Canales (crear, publicar, suscribir)
├── status.py       # Estados/Historias
├── privacy.py      # Privacidad
├── block.py        # Bloqueos
├── last.py         # Última conexión
├── location.py     # Ubicación (Near)
├── call.py         # Llamadas (TURN)
└── profile.py      # Cambio de @username</code></pre>

<h2>Uso Básico</h2>
<p>Cada función retorna una cadena XML lista para enviar por el socket XMPP.</p>
<pre><code class="language-python">from todus.stanzas import private, group, presence, utils

# Mensaje privado
xml = private.message("5351111111@im.todus.cu", "Hola")
sock.send(xml.encode())

# Mensaje de grupo
xml = group.group_message("grupo@muclight.im.todus.cu", "Hola grupo")

# Presencia
xml = presence.presence("Online", priority=5)</code></pre>

<h2>Módulos Destacados</h2>

<h3><code>private.py</code> – Mensajes Privados</h3>
<table>
    <thead>
        <tr><th>Función</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>message(to, body, msg_id, msg_type, reply_to_id)</code></td><td>Texto.</td></tr>
        <tr><td><code>edit_message(to, new_body, original_msg_id, edit_id, reply_to_id)</code></td><td>Edición.</td></tr>
        <tr><td><code>file_message(to, url, file_type, caption, msg_id, file_name, file_size, reply_to_id)</code></td><td>Archivo.</td></tr>
        <tr><td><code>image_message(...)</code></td><td>Imagen.</td></tr>
        <tr><td><code>image_message_simple(...)</code></td><td>Imagen simple.</td></tr>
        <tr><td><code>button_message(to, text, buttons, msg_id, reply_to_id)</code></td><td>Botones.</td></tr>
        <tr><td><code>contact_message(...)</code></td><td>Contacto.</td></tr>
        <tr><td><code>sticker_message(...)</code></td><td>Sticker.</td></tr>
        <tr><td><code>video_message(...)</code></td><td>Video.</td></tr>
        <tr><td><code>delete_message(...)</code></td><td>Eliminación.</td></tr>
        <tr><td><code>location_message(...)</code></td><td>Ubicación.</td></tr>
        <tr><td><code>event_message(...)</code></td><td>Evento.</td></tr>
    </tbody>
</table>
<p><strong>Estructura de un botón:</strong></p>
<pre><code class="language-python">button = {
    "text": "Enviar",
    "command": "cmd_type_send",
    "data": "Hola",
    "size": "0.82",        # FULL
    "color": "primary",    # opcional
    "row": True            # opcional
}</code></pre>

<h3><code>group.py</code> – Mensajes de Grupo</h3>
<p>Similar a <code>private.py</code> pero con <code>t='gc'</code> y destinados a JID de grupo.</p>
<p>Además incluye funciones para administración:</p>
<table>
    <thead>
        <tr><th>Función</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>group_update_name(to, name, msg_id)</code></td><td>Cambiar nombre.</td></tr>
        <tr><td><code>group_update_subject(to, subject, msg_id)</code></td><td>Cambiar asunto.</td></tr>
        <tr><td><code>group_update_avatar(to, avatar_url, msg_id)</code></td><td>Cambiar avatar.</td></tr>
        <tr><td><code>group_update_avatar_thumbnail(to, thumbnail_url, msg_id)</code></td><td>Cambiar miniatura.</td></tr>
        <tr><td><code>group_leave_iq(to, msg_id)</code></td><td>Salir.</td></tr>
        <tr><td><code>group_get_link_iq(to, msg_id)</code></td><td>Obtener enlace.</td></tr>
        <tr><td><code>group_set_link_iq(to, msg_id)</code></td><td>Revocar enlace.</td></tr>
        <tr><td><code>group_get_members_iq(to, msg_id)</code></td><td>Lista miembros.</td></tr>
        <tr><td><code>group_set_members_iq(to, affiliations, msg_id)</code></td><td>Modificar roles.</td></tr>
    </tbody>
</table>

<h3><code>presence.py</code></h3>
<table>
    <thead>
        <tr><th>Función</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>presence(status, priority, show, caps)</code></td><td>Presencia estándar.</td></tr>
        <tr><td><code>muc_presence(group_jid, nickname)</code></td><td>Unirse a grupo.</td></tr>
        <tr><td><code>muc_unavailable(group_jid)</code></td><td>Salir de grupo.</td></tr>
    </tbody>
</table>

<h3><code>utils.py</code></h3>
<table>
    <thead>
        <tr><th>Función</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>iq(type_, iq_id, payload, to)</code></td><td>IQ genérico.</td></tr>
        <tr><td><code>build_iq(type_, to, query)</code></td><td>IQ con ID autogenerado.</td></tr>
        <tr><td><code>ping(ping_id)</code></td><td>Ping XMPP.</td></tr>
        <tr><td><code>chat_state(to, state, msg_id, msg_type)</code></td><td>Estado de escritura.</td></tr>
        <tr><td><code>receipt(to, msg_id, receipt_id, msg_type)</code></td><td>ACK de entrega.</td></tr>
        <tr><td><code>read_receipt(to, msg_id, receipt_id, msg_type)</code></td><td>ACK de lectura.</td></tr>
        <tr><td><code>ack(msg_id, to)</code></td><td>TDACK.</td></tr>
        <tr><td><code>keepalive()</code></td><td>Espacio en blanco.</td></tr>
        <tr><td><code>stream_open(host)</code></td><td>Inicio de stream.</td></tr>
        <tr><td><code>stream_restart(host)</code></td><td>Reinicio de stream.</td></tr>
        <tr><td><code>stream_close()</code></td><td>Cierre de stream.</td></tr>
        <tr><td><code>sasl_auth(authstr)</code></td><td>Autenticación SASL PLAIN.</td></tr>
        <tr><td><code>bind(iq_id)</code></td><td>Resource bind.</td></tr>
        <tr><td><code>mam_query(query_id, since, before, limit)</code></td><td>MAM (archivo de mensajes).</td></tr>
        <tr><td><code>upload_query(iq_id, size, file_type, persistent, file_name)</code></td><td>Reserva de subida.</td></tr>
        <tr><td><code>download_query(iq_id, url)</code></td><td>Resolución de descarga.</td></tr>
    </tbody>
</table>

<h3>Canales, Estados, Privacidad, etc.</h3>
<p>Estos módulos generan stanzas IQ para sus respectivos dominios. Todas las funciones reciben parámetros específicos y retornan XML con <code>msg_id</code> autogenerado.</p>
<p>Ejemplo con canales:</p>
<pre><code class="language-python">from todus.stanzas import channels

xml = channels.create_channel_iq(
    name="Mi Canal",
    link="micanal",
    public=1,
    desc="Descripción",
    picture="https://...",
    subs=["5351111111", "5352222222"]
)</code></pre>

<h2>Uso Avanzado: Envío Directo</h2>
<p>Puedes enviar stanzas manualmente si necesitas un control total:</p>
<pre><code class="language-python">with client._xmpp_session(client.token) as sock:
    sock.send(xml.encode())</code></pre>