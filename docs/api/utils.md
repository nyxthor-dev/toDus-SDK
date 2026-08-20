<!-- docs/api/utils.md -->
<h1>Utilidades</h1>
<p>El módulo <code>util.py</code> proporciona funciones auxiliares para normalización, escape, JWT, dimensiones de imagen, etc.</p>

<h2>Funciones de Normalización</h2>

<h3><code>normalize_phone(phone: str) -> str</code></h3>
<p>Normaliza un número cubano al formato <code>53XXXXXXXX</code>.</p>
<pre><code class="language-python">normalize_phone("+5351234567")   # "5351234567"
normalize_phone("51234567")      # "5351234567"</code></pre>

<h3><code>build_jid(phone: str) -> str</code></h3>
<p>Construye un JID ToDus.</p>
<pre><code class="language-python">build_jid("5312345678")  # "5312345678@im.todus.cu"</code></pre>

<h3><code>parse_jid(jid: str) -> tuple[str, str]</code></h3>
<p>Extrae número de teléfono y resource de un JID.</p>
<pre><code class="language-python">parse_jid("5312345678@im.todus.cu/resource")
# ("5312345678", "resource")</code></pre>

<h2>Generación de Tokens</h2>

<h3><code>generate_token(length: int = 8) -> str</code></h3>
<p>Genera un token alfanumérico criptográficamente seguro (usando <code>secrets</code>).</p>
<pre><code class="language-python">token = generate_token(16)  # "aB3dEfGhIjKlMnOp"</code></pre>

<h2>Escape XML</h2>

<h3><code>escape_xml(text: str) -> str</code></h3>
<p>Escapa caracteres especiales XML (<code>&amp;</code>, <code>&lt;</code>, <code>&gt;</code>, <code>'</code>).</p>
<pre><code class="language-python">escape_xml("Hola & adiós")  # "Hola &amp; adiós"</code></pre>

<h3><code>unescape_xml(text: str) -> str</code></h3>
<p>Revierte el escape XML.</p>
<pre><code class="language-python">unescape_xml("Hola &amp; adiós")  # "Hola & adiós"</code></pre>

<h2>JWT</h2>

<h3><code>jwt_decode_payload(token: str) -> dict</code></h3>
<p>Decodifica el payload de un JWT sin verificar la firma.</p>
<pre><code class="language-python">payload = jwt_decode_payload(token)
# {"username": "5312345678", "exp": 1234567890, ...}</code></pre>

<h2>Tiempo</h2>

<h3><code>timestamp_ms() -> int</code></h3>
<p>Retorna el timestamp actual en milisegundos.</p>
<pre><code class="language-python">ts = timestamp_ms()  # 1700000000000</code></pre>

<h2>Formato de Tamaños</h2>

<h3><code>format_size(size_bytes: int) -> str</code></h3>
<p>Formatea bytes a unidades humanas (B, KB, MB, GB).</p>
<pre><code class="language-python">format_size(1500000)  # "1.4 MB"</code></pre>

<h2>Dimensiones de Imagen</h2>

<h3><code>get_image_dimensions(data: bytes) -> tuple[int, int]</code></h3>
<p>Extrae ancho y alto de imágenes JPEG o PNG sin decodificar completamente.</p>
<pre><code class="language-python">with open("foto.jpg", "rb") as f:
    data = f.read()
width, height = get_image_dimensions(data)
print(f"{width}x{height}")</code></pre>

<h2>BlurHash</h2>

<h3><code>generate_blurhash(width: int, height: int) -> str</code></h3>
<p>Genera un BlurHash genérico basado en dimensiones (placeholder).</p>
<pre><code class="language-python">hash = generate_blurhash(800, 600)
# "LFE_@w00ay00ay00ay00ay00ay00ay"</code></pre>

<h2>Sanitización de Nombres de Archivo</h2>

<h3><code>sanitize_filename(filename: str, file_type: int = 0) -> str</code></h3>
<p>Limpia caracteres problemáticos y añade la extensión correcta según el tipo de archivo.</p>
<table>
    <thead>
        <tr><th><code>FileType</code></th><th>Extensión</th></tr>
    </thead>
    <tbody>
        <tr><td><code>PICTURE</code></td><td><code>.jpg</code></td></tr>
        <tr><td><code>VIDEO</code></td><td><code>.mp4</code></td></tr>
        <tr><td><code>AUDIO</code></td><td><code>.mp3</code></td></tr>
        <tr><td><code>VOICE</code></td><td><code>.opus</code></td></tr>
        <tr><td><code>FILE</code></td><td><code>.bin</code></td></tr>
        <tr><td><code>PROFILE</code></td><td><code>.jpg</code></td></tr>
    </tbody>
</table>
<pre><code class="language-python">sanitize_filename("foto/extraña?.jpg", FileType.PICTURE)  # "foto_extra_a_.jpg"
sanitize_filename("sin_extension", FileType.VIDEO)        # "sin_extension.mp4"</code></pre>