<!-- docs/api/types_constants.md -->
<h1>Tipos y Constantes</h1>

<h2>Constantes (<code>constants.py</code>)</h2>
<pre><code class="language-python">XMPP_HOST = "im.todus.cu"
XMPP_PORT = 5222
MUCLIGHT_HOST = "muclight.im.todus.cu"
AUTH_VERSION_NAME = "2.1.2"
AUTH_VERSION_CODE = "30102"
BUFFER_SIZE = 1024 * 1024
KEEPALIVE_INTERVAL = 25
DEFAULT_TIMEOUT = 15</code></pre>

<h2>Enumeraciones (<code>types.py</code>)</h2>

<h3><code>FileType</code> (IntEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>FILE</code></td><td>0</td><td>Archivo genérico.</td></tr>
        <tr><td><code>VOICE</code></td><td>1</td><td>Nota de voz.</td></tr>
        <tr><td><code>AUDIO</code></td><td>2</td><td>Audio (música).</td></tr>
        <tr><td><code>VIDEO</code></td><td>3</td><td>Video.</td></tr>
        <tr><td><code>PICTURE</code></td><td>4</td><td>Imagen.</td></tr>
        <tr><td><code>PROFILE</code></td><td>5</td><td>Avatar de perfil.</td></tr>
        <tr><td><code>PROFILE_THUMBNAIL</code></td><td>6</td><td>Miniatura de avatar.</td></tr>
    </tbody>
</table>

<h3><code>ChatState</code> (StrEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th></tr>
    </thead>
    <tbody>
        <tr><td><code>COMPOSING</code></td><td><code>"composing"</code></td></tr>
        <tr><td><code>PAUSED</code></td><td><code>"paused"</code></td></tr>
        <tr><td><code>ACTIVE</code></td><td><code>"active"</code></td></tr>
        <tr><td><code>GONE</code></td><td><code>"gone"</code></td></tr>
        <tr><td><code>INACTIVE</code></td><td><code>"inactive"</code></td></tr>
    </tbody>
</table>

<h3><code>MessageType</code> (StrEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th></tr>
    </thead>
    <tbody>
        <tr><td><code>CHAT</code></td><td><code>"chat"</code></td></tr>
        <tr><td><code>GROUPCHAT</code></td><td><code>"groupchat"</code></td></tr>
        <tr><td><code>ERROR</code></td><td><code>"error"</code></td></tr>
        <tr><td><code>HEADLINE</code></td><td><code>"headline"</code></td></tr>
        <tr><td><code>NORMAL</code></td><td><code>"normal"</code></td></tr>
    </tbody>
</table>

<h3><code>PresenceShow</code> (StrEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th></tr>
    </thead>
    <tbody>
        <tr><td><code>CHAT</code></td><td><code>"chat"</code></td></tr>
        <tr><td><code>AWAY</code></td><td><code>"away"</code></td></tr>
        <tr><td><code>XA</code></td><td><code>"xa"</code></td></tr>
        <tr><td><code>DND</code></td><td><code>"dnd"</code></td></tr>
    </tbody>
</table>

<h3><code>ButtonSize</code> (StrEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>FULL</code></td><td><code>"0.82"</code></td><td>Botón ancho completo.</td></tr>
        <tr><td><code>HALF</code></td><td><code>"0.5"</code></td><td>Botón mitad de ancho.</td></tr>
    </tbody>
</table>

<h3><code>ButtonCommand</code> (StrEnum)</h3>
<table>
    <thead>
        <tr><th>Miembro</th><th>Valor</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>SEND</code></td><td><code>"cmd_type_send"</code></td><td>Envía el texto al chat.</td></tr>
        <tr><td><code>URL</code></td><td><code>"cmd_type_url"</code></td><td>Abre una URL.</td></tr>
        <tr><td><code>COPY</code></td><td><code>"cmd_type_copy"</code></td><td>Copia texto al portapapeles.</td></tr>
        <tr><td><code>CALL</code></td><td><code>"cmd_type_call"</code></td><td>Inicia una llamada.</td></tr>
    </tbody>
</table>