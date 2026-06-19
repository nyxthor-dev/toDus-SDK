<h1>📱 todus-lib</h1>

<p><strong>Cliente Python para ToDus</strong> — la plataforma de mensajería instantánea cubana. Soporta chat privado, grupos MUC Light, archivos, imágenes, videos, stickers, botones interactivos y más.</p>

<ul>
  <li><strong>Versión:</strong> 1.3.0</li>
  <li><strong>Python:</strong> >= 3.8</li>
  <li><strong>Autor:</strong> OrionWolf</li>
  <li><strong>Credits:</strong> <a href="https://github.com/ElJoker63" target="_blank" rel="noopener noreferrer">ElJoker63</a></li>
</ul> 

<hr>

<h2>📦 Instalación</h2>

<pre><code>pip install requests
python setup.py install</code></pre>

<p>O directamente desde la carpeta:</p>

<pre><code>pip install -e .</code></pre>

<hr>

<h2>🔐 Autenticación (¡Importante!)</h2>

<p>ToDus no usa contraseñas elegidas por el usuario. El proceso de autenticación tiene dos pasos:</p>

<ol>
  <li>Obtener un token largo (96 caracteres) mediante validación por SMS.</li>
  <li>Usar ese token para hacer login y obtener un JWT de sesión, que se usa para todas las comunicaciones.</li>
</ol>

<p>El cliente <code>ToDusClient2</code> guarda ese token largo en el atributo <code>password</code> (nombre histórico), pero en la práctica debes entenderlo como <code>auth_token</code>.</p>

<h3>🔹 Flujo para primera vez (SMS)</h3>

<pre><code>from todus import ToDusClient2

client = ToDusClient2(phone_number="535xxxxxxx")  # sin password aún

# 1. Pedir código SMS
client.request_code()   # te llega un PIN de 6 dígitos

# 2. Validar el código
client.validate_code("123456")
# Ahora client.password contiene el token largo (96 caracteres)
# ¡Guárdalo en un lugar seguro para futuras sesiones!

# 3. Obtener el JWT de sesión
client.login()   # ahora client.logged == True</code></pre>

<h3>🔹 Si ya tienes el token largo (de una sesión anterior)</h3>

<pre><code>client = ToDusClient2(phone_number="535xxxxxxx", password="ese_token_largo_que_guardaste")
client.login()   # obtiene el JWT internamente</code></pre>

<p><strong>⚠️ Importante:</strong> Nunca pases un JWT directamente al constructor. El cliente se encarga de renovarlo automáticamente cuando expira. El parámetro <code>password</code> espera el token largo de 96 caracteres.</p>

<hr>

<h2>🚀 Uso Rápido</h2>

<h3>Enviar mensajes (privados y grupos automáticamente)</h3>

<pre><code># Asumiendo que ya hiciste login
client.send_message("535yyyyyyy", "¡Hola mundo!")   # privado
client.send_message("mi-grupo-id", "Hola grupo!")   # grupo (auto-detectado)</code></pre>

<h3>Enviar imagen (con subida previa)</h3>

<pre><code>from todus import FileType

# 1. Subir la imagen
with open("foto.jpg", "rb") as f:
    image_data = f.read()
url = client.upload_file(image_data, FileType.PICTURE)

# 2. Enviar el mensaje con la imagen
client.send_image_message(
    "535yyyyyyy",
    url=url,
    file_name="foto.jpg",
    file_size=len(image_data),
    caption="Mi foto"
)</code></pre>

<h3>Escuchar mensajes entrantes</h3>

<pre><code>def on_message(msg):
    if msg.get("body"):
        print(f"{msg['from']}: {msg['body']}")

client.listen_messages(on_message)   # bucle infinito</code></pre>

<hr>

<h2>🤖 Bot de Ejemplo</h2>

<p>En la carpeta <code>examples/</code> encontrarás un bot funcional con comandos:</p>

<table>
  <thead>
    <tr>
      <th>Comando</th>
      <th>Respuesta</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><code>/start</code></td><td>Mensaje de bienvenida con lista de comandos</td></tr>
    <tr><td><code>/info</code></td><td>Información sobre la librería</td></tr>
    <tr><td><code>/ping</code></td><td><code>pong</code></td></tr>
  </tbody>
</table>

<p>Ejecútalo con:</p>

<pre><code>export TODUS_PHONE=535xxxxxxx
export TODUS_AUTH_TOKEN=token_largo_de_96_caracteres
python examples/bot.py</code></pre>

<hr>

<h2>📡 Tipos de Mensaje Soportados</h2>

<p>La librería soporta los siguientes tipos de mensaje:</p>

<table>
  <thead>
    <tr>
      <th>Tipo</th>
      <th>Método (ToDusClient2)</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Texto</td><td><code>send_message(to, body)</code></td></tr>
    <tr><td>Imagen</td><td><code>send_image_message(to, url, file_name, file_size, ...)</code></td></tr>
    <tr><td>Video</td><td><code>send_video_message(to, url, video_id, file_name, ...)</code></td></tr>
    <tr><td>Archivo</td><td><code>send_file_message(to, url, file_type, ...)</code></td></tr>
    <tr><td>Sticker</td><td><code>send_sticker_message(to, sticker_id, ...)</code></td></tr>
    <tr><td>Contacto</td><td><code>send_contact_message(to, contact_id, ...)</code></td></tr>
    <tr><td>Botones</td><td><code>send_button_message(to, text, buttons)</code></td></tr>
    <tr><td>Editar</td><td><code>edit_message(to, new_body, original_msg_id)</code></td></tr>
    <tr><td>Eliminar</td><td><code>delete_message(to, message_id)</code></td></tr>
  </tbody>
</table>

<p><strong>Auto-detección de destino:</strong> si el <code>to</code> no es un número cubano (10 dígitos empezando por 53), se asume que es un <code>group_id</code> y el mensaje se envía al grupo automáticamente.</p>

<hr>

<h2>👥 Grupos MUC Light</h2>

<pre><code># Unirse a un grupo
client.groups.join("mi-grupo-id")

# Enviar mensaje al grupo (auto-detectado)
client.send_message("mi-grupo-id", "Hola grupo!")

# Callback específico para mensajes de ese grupo
def on_group_msg(msg):
    print(f"{msg['sender_phone']}: {msg['body']}")

client.groups.on_group_message("mi-grupo-id", on_group_msg)

# Salir del grupo
client.groups.leave("mi-grupo-id")</code></pre>

<hr>

<h2>📤 Subir y Descargar Archivos</h2>

<pre><code># Subir cualquier archivo
with open("documento.pdf", "rb") as f:
    url = client.upload_file(f.read(), FileType.FILE)

# Descargar a una carpeta
size, path = client.download_file_to_folder(url, "./descargas")
print(f"Descargado {size} bytes en {path}")</code></pre>

<hr>

<h2>⚠️ Excepciones</h2>

<table>
  <thead>
    <tr>
      <th>Excepción</th>
      <th>Cuándo ocurre</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><code>AuthenticationError</code></td><td>Credenciales inválidas o falta autenticación</td></tr>
    <tr><td><code>TokenExpiredError</code></td><td>El token JWT expiró (el cliente lo renueva automáticamente si usas ToDusClient2)</td></tr>
    <tr><td><code>ConnectionLostError</code></td><td>Se perdió la conexión XMPP</td></tr>
    <tr><td><code>UploadError</code></td><td>Error al subir/descargar archivo</td></tr>
    <tr><td><code>GroupError</code></td><td>Error en operación de grupo</td></tr>
    <tr><td><code>ParseError</code></td><td>Stanza malformada</td></tr>
  </tbody>
</table>

<hr>

<h2>🗂️ Estructura del Proyecto</h2>

<pre><code>todus-lib/
├── todus/                  # Código fuente de la librería
│   ├── __init__.py         # Exports principales
│   ├── client.py           # ToDusClient y ToDusClient2
│   ├── group.py            # Soporte para grupos MUC Light
│   ├── stanza.py           # Constructor de stanzas XMPP
│   ├── parser.py           # Parser incremental de stanzas
│   ├── types.py            # Enums (FileType, ChatState, etc.)
│   ├── util.py             # Utilidades (JID, XML, JWT, etc.)
│   ├── constants.py        # Hosts, puertos, versiones
│   ├── errors.py           # Excepciones personalizadas
│   └── setup.py            # Configuración de setuptools
├── examples/               # Ejemplos de uso
│   └── bot.py              # Bot con comandos
└── README.md               # Este archivo</code></pre>

<hr>

<h2>🔗 Recursos</h2>

- **ToDus oficial:** [ToDus](https://web.todus.cu)
- **Apklis:** [Apklis](https://www.apklis.cu/application/cu.todus.android)
