<!-- docs/client/overview.md -->
<h1>Visión General del Cliente ToDus</h1>
<p>El módulo <code>client</code> es el núcleo del SDK. Contiene la lógica de conexión XMPP, autenticación y todas las funcionalidades de la plataforma.</p>

<h2>Arquitectura</h2>
<p>El cliente principal <code>ToDusClient2</code> combina múltiples <strong>mixins</strong> que agrupan funcionalidades específicas.</p>
<pre><code>ToDusClient2
├── ToDusClientBase          # Socket XMPP, Handshake, Sesiones
├── ToDusAuthMixin           # Autenticación (login, código SMS)
├── ToDusMessageMixin        # Mensajería (texto, archivos, etc.)
├── ToDusFileMixin           # Subida/descarga de archivos
├── ToDusProfileMixin        # Perfil y avatar
├── ToDusChannelMixin        # Canales públicos/privados
├── ToDusStatusMixin         # Estados/Historias
├── ToDusPrivacyMixin        # Configuración de privacidad
├── ToDusBlockMixin          # Bloqueo de usuarios
├── ToDusLastMixin           # Última conexión
├── ToDusLocationMixin       # Ubicación (Near)
└── ToDusCallMixin           # Señalización de llamadas</code></pre>

<h2>Clases Principales</h2>

<h3><code>ToDusClient2</code> (Recomendado)</h3>
<p>Clase <strong>stateful</strong> que mantiene la sesión, el token y el número de teléfono.</p>
<p><strong>Constructor:</strong></p>
<pre><code class="language-python">ToDusClient2(
    phone_number: str,
    password: str = "",
    proxy: Optional[str] = None,
    verify_ssl: bool = False,
    **kwargs
)</code></pre>
<p><strong>Propiedades:</strong></p>
<ul>
    <li><code>token</code> – JWT actual.</li>
    <li><code>logged</code> – <code>bool</code> indica si hay sesión activa.</li>
    <li><code>phone_number</code> – Número normalizado.</li>
    <li><code>groups</code> – Instancia de <code>GroupClient</code>.</li>
</ul>
<p><strong>Métodos principales:</strong></p>
<ul>
    <li><code>login()</code> → Inicia sesión.</li>
    <li><code>send_message(to, body, reply_to_id)</code> → Envía texto.</li>
    <li><code>upload_file(data, file_type, progress_callback, file_name)</code> → Sube archivo.</li>
    <li><code>listen_messages(callback)</code> → Bucle de escucha.</li>
</ul>

<h3><code>ToDusClient</code> (Stateless)</h3>
<p>Clase que hereda todos los mixins pero <strong>no</strong> mantiene estado. Todos los métodos requieren <code>token</code> como primer argumento. Útil para aplicaciones que manejan múltiples cuentas simultáneamente.</p>
<pre><code class="language-python"># Ejemplo stateless
client = ToDusClient()
token = client.login("5312345678", "password")
client.send_message(token, "5387654321@im.todus.cu", "Hola")</code></pre>

<h2>Detección Automática de Grupos</h2>
<p><code>ToDusClient2</code> incluye un mecanismo de detección inteligente:</p>
<ul>
    <li>Si <code>to_phone</code> es un número de 10 dígitos empezando por <code>53</code> → se envía como mensaje privado.</li>
    <li>Si no cumple con el patrón → se trata como ID de grupo y se reenvía a <code>client.groups</code>.</li>
</ul>
<p>Esto permite usar los mismos métodos (<code>send_message</code>, <code>send_image_message</code>, etc.) indistintamente para privados o grupos.</p>

<h2>Ciclo de Vida de la Conexión</h2>
<ol>
    <li><strong>Autenticación:</strong> <code>login()</code> obtiene el token JWT.</li>
    <li><strong>Handshake:</strong> Se establece el socket XMPP y se negocia SASL.</li>
    <li><strong>Sesión:</strong> Se envía presencia inicial y se mantiene el stream.</li>
    <li><strong>Escucha:</strong> <code>listen_messages()</code> entra en un bucle recibiendo stanzas.</li>
    <li><strong>Keepalive:</strong> Envía pings cada 25 segundos para mantener la conexión.</li>
    <li><strong>Reconexión:</strong> Si la conexión se pierde, <code>listen_messages</code> espera 15s y reintenta.</li>
</ol>

<h2>Acceso a Mixins</h2>
<p>Todos los mixins están disponibles directamente en la instancia de <code>ToDusClient2</code>. Por ejemplo:</p>
<pre><code class="language-python">client.send_message(...)        # ToDusMessageMixin
client.upload_file(...)         # ToDusFileMixin
client.update_profile(...)      # ToDusProfileMixin
client.block_user(...)          # ToDusBlockMixin
client.set_location(...)        # ToDusLocationMixin
client.start_call(...)          # ToDusCallMixin</code></pre>
<p>Consulta la página <strong><a href="mixins.md">Mixins</a></strong> para la referencia completa de todos los métodos.</p>