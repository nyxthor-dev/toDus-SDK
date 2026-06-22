<!-- docs/quickstart.md -->
<h1>Inicio Rápido</h1>
<p>Esta guía te muestra los escenarios más comunes usando el SDK.</p>

<h2>1. Cliente Básico (Sin Cola)</h2>
<pre><code class="language-python">from todus import ToDusClient2

# 1. Crear cliente

client = ToDusClient2(phone_number="5312345678", password="mi_clave")

# 2. Iniciar sesión

client.login()

# 3. Enviar mensaje privado

client.send_message("5387654321", "Hola, ¿cómo estás?")</code></pre>

<h2>2. Cliente con Cola Persistente</h2>
<p>Ideal para bots o aplicaciones que necesitan garantizar la entrega.</p>
<pre><code class="language-python">from todus import ToDusClientWithQueue

client = ToDusClientWithQueue(
    phone_number="5312345678",
    password="mi_clave",
    enable_queue=True,
    queue_db_path="~/.todus/messages.db"  # opcional
)

client.login()

# Registrar callbacks

def on_delivered(msg):
    print(f"✅ Entregado: {msg.msg_id}")

def on_failed(msg):
    print(f"❌ Falló: {msg.msg_id} - {msg.last_error}")

client.register_on_message_delivered(on_delivered)
client.register_on_message_failed(on_failed)

# Enviar y encolar

msg_id = client.send_message_queued("5387654321", "Mensaje con garantía")</code></pre>

<h2>3. Escuchar Mensajes Entrantes</h2>
<pre><code class="language-python">def handle_message(msg):
    # Ignorar mensajes de grupo si no interesan
    if msg.get("is_group"):
        return

    sender = msg.get("from")
    body = msg.get("body")
    if sender and body:
        print(f"De {sender}: {body}")

# Bucle infinito (bloquea el hilo)

client.listen_messages(client.token, handle_message)

# Si necesitas multitarea, ejecuta en un hilo

# import threading

# threading.Thread(target=client.listen_messages, args=(client.token, handle_message), daemon=True).start()</code></pre>

<h2>4. Trabajar con Archivos</h2>
<h3>Subir y enviar una imagen</h3>
<pre><code class="language-python">from todus.types import FileType

# Leer imagen

with open("mi_foto.jpg", "rb") as f:
    image_data = f.read()

# Subir a servidores ToDus

url = client.upload_file(
    image_data,
    file_type=FileType.PICTURE,
    file_name="mi_foto.jpg"
)

# Enviar la imagen

client.send_image_message(
    to_phone="5387654321",
    url=url,
    file_name="mi_foto.jpg",
    file_size=len(image_data),
    width=800,
    height=600,
    caption="Mi foto"
)</code></pre>

<h3>Descargar un archivo</h3>
<pre><code class="language-python"># Descargar a una carpeta
size, path = client.download_file_to_folder(
    url="https://...",
    folder="./descargas/",
    filename="documento.pdf"
)
print(f"Descargado {size} bytes en {path}")</code></pre>

<h2>5. Trabajar con Grupos</h2>
<pre><code class="language-python"># Unirse a un grupo
client.groups.join("id_del_grupo", nickname="MiApodo")

# Enviar mensaje al grupo

client.groups.send_message("id_del_grupo", "¡Hola a todos!")

# Obtener lista de miembros

msg_id = client.groups.get_members("id_del_grupo")

# Expulsar a un miembro

client.groups.kick_member("id_del_grupo", "5351111111")</code></pre>

<h2>6. Actualizar Perfil</h2>
<pre><code class="language-python"># Actualizar alias y biografía
client.update_profile(alias="MiNombre", bio="Desarrollador Python")

# Subir avatar (desde archivo)

profile_url, thumb_url = client.upload_avatar_from_file("avatar.jpg")
client.update_profile(picture_url=profile_url, thumbnail_url=thumb_url)</code></pre>

<h2>7. Manejo de Estados (Historias)</h2>
<pre><code class="language-python">import json

# Publicar un estado

status_content = {
    "type": "text",
    "text": "Mi estado del día",
    "background": "#FF0000"
}
client.publish_status(json.dumps(status_content))

# Seguir a un usuario

client.follow_user("5312345678")</code></pre>

<div class="admonition tip">
    <p class="admonition-title">Consejo</p>
    <p>Todos los métodos que devuelven <code>msg_id</code> son asíncronos. La respuesta llegará a través del callback que registres en <code>listen_messages</code>. Para obtener respuestas de <code>get_members</code> o <code>get_invite_link</code>, utiliza el método <code>parse_members_response</code> o <code>parse_invite_link_response</code> sobre la stanza cruda (<code>msg["raw"]</code>).</p>
</div>
