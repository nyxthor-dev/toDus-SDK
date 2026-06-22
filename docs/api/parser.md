<!-- docs/api/parser.md -->
<h1>Parser de Stanzas</h1>
<p>El módulo <code>parser.py</code> proporciona herramientas para parsear las stanzas XML entrantes desde el socket XMPP, manejando fragmentación TCP.</p>

<h2>Funciones de Parseo</h2>

<h3><code>parse_todus_message(stanza: str) -> dict</code></h3>
<p>Parsea una stanza <code>&lt;m&gt;</code> de ToDus y devuelve un diccionario con todos los campos extraídos.</p>
<p><strong>Ejemplo de salida:</strong></p>
<pre><code>{
    "from": "5312345678@im.todus.cu",
    "to": "5387654321@im.todus.cu",
    "id": "a1b2c3d4",
    "type": "c",
    "body": "Hola mundo",
    "is_group": False,
    "buttons": [],
    "reply_to": "",
    "raw": "&lt;m ...&gt;...&lt;/m&gt;"
}</code></pre>
<p><strong>Campos principales:</strong></p>
<ul>
    <li><code>from</code>, <code>to</code>, <code>id</code>, <code>type</code>, <code>original_id</code></li>
    <li><code>body</code> – Texto del mensaje.</li>
    <li><code>is_group</code> – <code>True</code> si es mensaje de grupo.</li>
    <li><code>group_id</code>, <code>sender_phone</code> – Si es grupo.</li>
    <li><code>reply_to</code> – ID del mensaje al que se responde.</li>
    <li><code>url</code>, <code>file_name</code>, <code>file_size</code>, <code>file_id</code> – Archivos.</li>
    <li><code>image_width</code>, <code>image_height</code>, <code>image_thumbnail</code> – Imágenes.</li>
    <li><code>video_url</code>, <code>video_name</code>, <code>video_duration</code>, <code>video_width</code>, <code>video_height</code>, <code>video_thumbnail</code> – Videos.</li>
    <li><code>sticker_id</code>, <code>sticker_name</code>, <code>sticker_pack</code>, <code>sticker_hash</code> – Stickers.</li>
    <li><code>contact_id</code>, <code>contact_name</code>, <code>contact_phone</code> – Contactos.</li>
    <li><code>location_lat</code>, <code>location_lon</code>, <code>location_zoom</code>, <code>location_text</code> – Ubicación.</li>
    <li><code>event_title</code>, <code>event_start</code>, <code>event_end</code>, <code>event_all_day</code>, <code>event_ics</code> – Eventos.</li>
    <li><code>buttons</code> – Lista de diccionarios con <code>text</code>, <code>command</code>, <code>data</code>, <code>size</code>.</li>
    <li><code>edited</code> – ID de edición.</li>
    <li><code>deleted</code> – ID de eliminación.</li>
    <li><code>receipt</code>, <code>receipt_type</code> – Confirmaciones (<code>delivered</code> / <code>read</code>).</li>
    <li><code>chat_state</code> – <code>composing</code> o <code>paused</code>.</li>
    <li><code>offline_ts</code> – Timestamp de mensaje offline.</li>
    <li><code>raw</code> – Stanza original.</li>
</ul>

<h3><code>parse_presence(stanza: str) -> dict</code></h3>
<p>Parsea presencia XMPP.</p>
<pre><code>{
    "from": "...",
    "to": "...",
    "id": "...",
    "status": "Online",
    "show": "chat",
    "priority": 5,
    "raw": "..."
}</code></pre>

<h3><code>parse_iq(stanza: str) -> dict</code></h3>
<p>Parsea stanzas IQ.</p>
<pre><code>{
    "from": "...",
    "to": "...",
    "id": "...",
    "type": "result" | "set" | "get",
    "error": "...",           # si existe
    "query": "...",           # contenido interno
    "upload_url": "...",      # si es respuesta de upload
    "download_url": "...",    # si es respuesta de upload
    "real_url": "...",        # si es respuesta de download
    "raw": "..."
}</code></pre>

<h3><code>parse_tdack(stanza: str) -> dict</code></h3>
<p>Parsea acknowledgment (<code>&lt;tdack&gt;</code>).</p>
<pre><code>{
    "type": "tdack",
    "message_id": "...",
    "raw": "..."
}</code></pre>

<h2><code>IncrementalParser</code></h2>
<p>Parser que maneja stanzas fragmentadas en múltiples paquetes TCP.</p>
<h3>Métodos</h3>
<ul>
    <li><code>feed(chunk: str) -> list[dict]</code> – Alimenta con nuevo chunk y retorna stanzas completas parseadas.</li>
    <li><code>reset()</code> – Limpia el buffer interno.</li>
</ul>
<p><strong>Uso Interno:</strong> El cliente <code>ToDusClientBase</code> utiliza este parser en <code>_listen_loop</code> para procesar el flujo continuo de datos.</p>
<pre><code class="language-python">parser = IncrementalParser()
stanzas = parser.feed(recv_data)
for stanza in stanzas:
    # Procesar cada stanza</code></pre>

<h2>Ejemplo de Uso Directo</h2>
<pre><code class="language-python">from todus.parser import parse_todus_message

raw = '&lt;m to="..." t="c" i="123" xmlns="jc"&gt;&lt;k xmlns="x8"/&gt;&lt;b&gt;Hola&lt;/b&gt;&lt;/m&gt;'
parsed = parse_todus_message(raw)
print(parsed["body"])  # "Hola"</code></pre>