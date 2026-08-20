<!-- docs/api/errors.md -->
<h1>Manejo de Errores</h1>
<p>Todas las excepciones del SDK heredan de la clase base <code>ToDusError</code>.</p>

<h2>Jerarquía de Excepciones</h2>
<pre><code>ToDusError
├── AuthenticationError     # Credenciales inválidas o sesión expirada.
├── TokenExpiredError       # Token JWT ya no es válido.
├── ConnectionLostError     # Conexión XMPP perdida inesperadamente.
├── MessageError            # Error al enviar o recibir mensaje.
├── UploadError             # Error en subida/descarga de archivo.
├── ParseError              # Error parseando stanza XMPP.
├── RateLimitError          # Demasiadas peticiones en poco tiempo.
├── StanzaError             # Stanza malformada o no soportada.
└── GroupError              # Error relacionado con grupos MUC Light.</code></pre>

<h2>Descripción Detallada</h2>

<h3><code>ToDusError</code></h3>
<p>Clase base para todos los errores del SDK.</p>

<h3><code>AuthenticationError</code></h3>
<p>Se lanza cuando:</p>
<ul>
    <li>Las credenciales (usuario/contraseña) son inválidas.</li>
    <li>La sesión no está autenticada y se intenta realizar una acción que lo requiere.</li>
</ul>
<pre><code class="language-python">try:
    client.login()
except AuthenticationError as e:
    print("Error de autenticación:", e)</code></pre>

<h3><code>TokenExpiredError</code></h3>
<p>Se lanza cuando el token JWT ha expirado y el servidor lo rechaza. El cliente debe volver a autenticarse.</p>

<h3><code>ConnectionLostError</code></h3>
<p>Se lanza cuando la conexión XMPP se cierra inesperadamente (timeout, servidor caído, etc.). <code>listen_messages</code> reintenta automáticamente después de 15 segundos.</p>

<h3><code>UploadError</code></h3>
<p>Se lanza durante la subida o descarga de archivos (errores HTTP, URLs inválidas, permisos, etc.).</p>

<h3><code>GroupError</code></h3>
<p>Se lanza cuando ocurre un problema específico con grupos MUC Light (no se puede unir, miembro inexistente, etc.).</p>

<h2>Ejemplo de Manejo de Errores</h2>
<pre><code class="language-python">from todus import ToDusClient2
from todus.errors import AuthenticationError, ConnectionLostError

try:
    client = ToDusClient2("5312345678", "password")
    client.login()
except AuthenticationError:
    print("Credenciales incorrectas")
except ConnectionLostError:
    print("Error de red")
except Exception as e:
    print(f"Error inesperado: {e}")</code></pre>

<h2>Buenas Prácticas</h2>
<ul>
    <li>Siempre envolver <code>login()</code> en un bloque <code>try/except</code> para manejar credenciales inválidas.</li>
    <li><code>listen_messages()</code> captura internamente <code>ConnectionLostError</code> y reintenta; si necesitas salir, implementa un mecanismo de bandera externo.</li>
    <li>Para operaciones de archivos, manejar <code>UploadError</code> para mostrar mensajes de error amigables.</li>
</ul>