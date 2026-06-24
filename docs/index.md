<!-- docs/index.md -->
<h1>ToDus SDK para Python</h1>

<p>Bienvenido a la documentación oficial del <strong>ToDus SDK</strong>, la biblioteca Python que te permite interactuar con la plataforma de mensajería y redes sociales cubana <strong>ToDus</strong>.</p>
<p>Este SDK implementa los protocolos XMPP y HTTP de ToDus, ofreciendo una API moderna, asíncrona y fácil de usar para desarrollar bots, aplicaciones de escritorio, integraciones y automatizaciones.</p>

<h2>🚀 Características Principales</h2>
<ul>
    <li><strong>Autenticación completa</strong> (contraseña o código SMS).</li>
    <li><strong>Mensajería privada</strong> con soporte para texto, imágenes, videos, stickers, ubicación, contactos y eventos.</li>
    <li><strong>Mensajería en grupos</strong> (MUC Light) con administración de miembros y roles.</li>
    <li><strong>Canales públicos y privados</strong> con suscripción y publicación.</li>
    <li><strong>Estados/Historias</strong> (StatusManager) con seguimiento de usuarios.</li>
    <li><strong>Subida y descarga de archivos</strong> con seguimiento de progreso.</li>
    <li><strong>Cola de mensajes persistente</strong> con SQLite, reintentos exponenciales y callbacks.</li>
    <li><strong>Soporte para proxies</strong> HTTP, SOCKS4 y SOCKS5.</li>
    <li><strong>Reconexión automática</strong> y Keepalive.</li>
</ul>

<h2>📦 Instalación Rápida</h2>
<pre><code class="language-bash">pip install todus-sdk</code></pre>

<h2>🧪 Primeros Pasos</h2>
<pre><code class="language-python">from todus import ToDusClientWithQueue

client = ToDusClientWithQueue("5312345678", "mi_contraseña")
client.login()

# Enviar un mensaje (con cola y reintentos)

msg_id = client.send_message_queued("5387654321", "¡Hola mundo!")

# Escuchar mensajes entrantes

def on_message(msg):
    print(f"{msg.get('from')}: {msg.get('body')}")

client.listen_messages(client.token, on_message)</code></pre>

<h2>🤝 Contribuir</h2>
<p>El SDK es de código abierto. Las contribuciones son bienvenidas.<br>
Visita nuestro repositorio en <a href="https://github.com/tu-usuario/todus-sdk">GitHub</a> para reportar issues o enviar pull requests.</p>
