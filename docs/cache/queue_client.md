<!-- docs/cache/queue_client.md -->
<h1>Cliente con Cola (ToDusClientWithQueue)</h1>
<p>Esta página detalla el uso específico de <code>ToDusClientWithQueue</code>, que combina todas las capacidades de <code>ToDusClient2</code> con la cola persistente.</p>

<h2>Constructor</h2>
<pre><code class="language-python">ToDusClientWithQueue(
    phone_number: str,
    password: str = "",
    enable_queue: bool = True,
    queue_db_path: Optional[str] = None,
    **kwargs
)</code></pre>
<p><strong>Parámetros:</strong></p>
<ul>
    <li><code>phone_number</code> – Número de teléfono (formato <code>53XXXXXXXX</code>).</li>
    <li><code>password</code> – Contraseña de la cuenta.</li>
    <li><code>enable_queue</code> – Activa/desactiva la cola (por defecto <code>True</code>).</li>
    <li><code>queue_db_path</code> – Ruta al archivo SQLite. Si es <code>None</code>, usa <code>~/.todus/messages.db</code>.</li>
    <li><code>**kwargs</code> – Se pasan a <code>ToDusClient2</code> (proxy, verify_ssl, etc.).</li>
</ul>

<h2>Método Estrella: <code>send_message_queued()</code></h2>
<pre><code class="language-python">def send_message_queued(self, to_phone: str, body: str, reply_to_id: str = "") -> str</code></pre>
<p><strong>Comportamiento:</strong></p>
<ol>
    <li>Detecta automáticamente si <code>to_phone</code> es un número privado o un grupo.</li>
    <li>Envía el mensaje.</li>
    <li>Lo encola en SQLite.</li>
    <li>Marca como <code>SENT</code> si el envío fue exitoso.</li>
    <li>Si falla, el worker automático lo reintentará.</li>
</ol>
<p><strong>Retorna:</strong> <code>msg_id</code> del mensaje.</p>

<h2>Registro de Callbacks</h2>
<pre><code class="language-python">client.register_on_message_delivered(callback)
client.register_on_message_read(callback)
client.register_on_message_failed(callback)</code></pre>
<p>Cada callback recibe un objeto <code>Message</code> como argumento.</p>

<h2>Estadísticas de la Cola</h2>
<pre><code class="language-python">stats = client.get_queue_stats()</code></pre>
<p><strong>Ejemplo de salida:</strong></p>
<pre><code>{
    'pending': 0,
    'sent': 2,
    'delivered': 5,
    'read': 3,
    'failed': 1,
    'total_pending': 0,
    'total_failed': 1,
    'worker_running': True
}</code></pre>

<h2>Limpieza Automática</h2>
<pre><code class="language-python"># Elimina mensajes con estado READ o DELIVERED de más de 30 días
deleted = client.cleanup_queue()
print(f"Limpiados {deleted} mensajes")</code></pre>

<h2>Ejemplo Avanzado con Progreso</h2>
<pre><code class="language-python">from todus import ToDusClientWithQueue
from todus.types import FileType

client = ToDusClientWithQueue("5312345678", "password")
client.login()

def on_progress(current, total):
    print(f"Subiendo: {current}/{total}")

# Subir archivo
image_data = open("foto.jpg", "rb").read()
url = client.upload_file(
    image_data,
    file_type=FileType.PICTURE,
    progress_callback=on_progress,
    file_name="foto.jpg"
)

# Enviar con cola
msg_id = client.send_message_queued(
    to_phone="5387654321",
    body="Mira mi foto",
    reply_to_id=""
)

# La entrega se maneja con callbacks
def on_delivered(msg):
    if msg.msg_id == msg_id:
        print("¡Foto entregada!")

client.register_on_message_delivered(on_delivered)</code></pre>

<h2>Consideraciones</h2>
<ul>
    <li>La cola <strong>no</strong> garantiza orden estricto de entrega, pero sí garantiza que cada mensaje se reintente hasta alcanzar <code>max_retries</code>.</li>
    <li>El worker de reintentos corre en un hilo <code>daemon</code>; se detiene automáticamente al finalizar el programa.</li>
    <li>Para detenerlo manualmente: <code>client.queue.stop_auto_retry_worker()</code>.</li>
</ul>