<!-- docs/groups.md -->
<h1>Grupos MUC Light</h1>
<p>El SDK soporta completamente los grupos <strong>MUC Light</strong> de ToDus a través de la propiedad <code>groups</code> de <code>ToDusClient2</code> y <code>ToDusClientWithQueue</code>.</p>

<h2>Acceso al Cliente de Grupos</h2>
<pre><code class="language-python">client = ToDusClient2("5312345678", "password")
client.login()

# Obtener instancia del GroupClient
groups = client.groups</code></pre>

<h2>Unirse y Salir de Grupos</h2>
<h3>Unirse</h3>
<pre><code class="language-python"># group_id es el identificador del grupo (ej: "mi_grupo")
groups.join(group_id, nickname="MiApodo")</code></pre>
<h3>Salir</h3>
<pre><code class="language-python">groups.leave(group_id)</code></pre>

<h2>Envío de Mensajes</h2>
<h3>Texto</h3>
<pre><code class="language-python">groups.send_message(group_id, "Hola a todos", reply_to_id="")</code></pre>
<h3>Imagen</h3>
<pre><code class="language-python">groups.send_image(
    group_id,
    url="https://...",
    file_name="foto.jpg",
    file_size=12345,
    width=800,
    height=600,
    thumbnail="...",
    caption="Mi foto",
    reply_to_id=""
)</code></pre>
<h3>Video</h3>
<pre><code class="language-python">groups.send_video(
    group_id,
    url="https://...",
    video_id="vid123",
    file_name="video.mp4",
    file_size=12345,
    duration=60,
    width=1280,
    height=720,
    thumbnail="...",
    caption="Mi video"
)</code></pre>
<h3>Sticker</h3>
<pre><code class="language-python">groups.send_sticker(
    group_id,
    sticker_id="stk1",
    sticker_name="feliz",
    sticker_pack="pack1",
    sticker_hash="abc123"
)</code></pre>
<h3>Contacto</h3>
<pre><code class="language-python">groups.send_contact(
    group_id,
    contact_id="c1",
    contact_name="Juan Pérez",
    contact_phone="5351234567"
)</code></pre>
<h3>Ubicación</h3>
<pre><code class="language-python">groups.send_location(
    group_id,
    lat=23.1136,
    lon=-82.3666,
    zoom=11.0,
    text="Mi ubicación"
)</code></pre>
<h3>Evento</h3>
<pre><code class="language-python">import time
start = int(time.time())
end = start + 3600

groups.send_event(
    group_id,
    title="Reunión",
    start=start,
    end=end,
    all_day=False,
    ics_data="BEGIN:VCALENDAR...",
    event_id="ev1"
)</code></pre>

<h2>Administración del Grupo</h2>
<h3>Cambiar Nombre</h3>
<pre><code class="language-python">groups.set_name(group_id, "Nuevo Nombre")</code></pre>
<h3>Cambiar Asunto/Descripción</h3>
<pre><code class="language-python">groups.set_subject(group_id, "Descripción del grupo")</code></pre>
<h3>Cambiar Avatar</h3>
<pre><code class="language-python">groups.set_avatar(group_id, "https://.../avatar.jpg", "https://.../thumb.jpg")</code></pre>
<h3>Obtener Enlace de Invitación</h3>
<pre><code class="language-python">msg_id = groups.get_invite_link(group_id)
# La respuesta llega por el callback de listen_messages
# Usar groups.parse_invite_link_response(msg["raw"]) para extraer el enlace</code></pre>
<h3>Revocar Enlace</h3>
<pre><code class="language-python">groups.revoke_invite_link(group_id)</code></pre>
<h3>Obtener Miembros</h3>
<pre><code class="language-python">msg_id = groups.get_members(group_id)
# Para parsear la respuesta:
# members = groups.parse_members_response(msg["raw"])
# members: {"5350000000": "participant", "5351111111": "moderator", ...}</code></pre>
<h3>Cambiar Rol de Miembro</h3>
<pre><code class="language-python">from todus import GroupRole

# Roles: "participant", "moderator", "owner", "none"
groups.set_member_role(group_id, "5351111111", GroupRole.MODERATOR)</code></pre>
<h3>Expulsar Miembro</h3>
<pre><code class="language-python">groups.kick_member(group_id, "5351111111")</code></pre>

<h2>Edición y Eliminación de Mensajes</h2>
<h3>Editar</h3>
<pre><code class="language-python">groups.edit_message(
    group_id,
    new_body="Nuevo texto",
    original_msg_id="id_del_mensaje_original"
)</code></pre>
<h3>Eliminar</h3>
<pre><code class="language-python">groups.delete_message(
    group_id,
    message_id="id_a_eliminar",
    body="Texto del mensaje (opcional)",
    media_xml="<image.../> (opcional)"
)</code></pre>

<h2>Callbacks por Grupo</h2>
<pre><code class="language-python">def on_group_msg(msg):
    print(f"Grupo {msg['group_id']}: {msg.get('body')}")

groups.on_group_message("mi_grupo", on_group_msg)</code></pre>

<h2>Eventos de Grupo</h2>
<p>El SDK detecta automáticamente eventos como entrada/salida de miembros.</p>
<pre><code class="language-python">def on_message(msg):
    if msg.get("is_group_event"):
        event = msg.get("event")
        if event == "joined":
            print("Alguien se unió")
        elif event == "left":
            print("Alguien se fue")
        elif event == "kicked":
            print("Alguien fue expulsado")

client.listen_messages(client.token, on_message)</code></pre>
<p><strong>Eventos disponibles (<code>GroupEvent</code>):</strong></p>
<ul>
    <li><code>MEMBER_JOINED</code></li>
    <li><code>MEMBER_LEFT</code></li>
    <li><code>MEMBER_KICKED</code></li>
    <li><code>MEMBER_BANNED</code></li>
    <li><code>SUBJECT_CHANGED</code></li>
    <li><code>ROOM_CREATED</code></li>
    <li><code>ROOM_DESTROYED</code></li>
</ul>