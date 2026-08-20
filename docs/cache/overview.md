<!-- docs/cache/overview.md -->
<h1>Cola de Mensajes Persistente (Cache)</h1>
<p>El módulo <code>cache</code> proporciona un sistema de cola de mensajes con almacenamiento en <strong>SQLite</strong>, reintentos automáticos con <strong>backoff exponencial</strong> y <strong>callbacks</strong> para eventos.</p>
<p>Este sistema es ideal para bots y aplicaciones que necesitan garantizar la entrega de mensajes incluso en entornos con conectividad inestable.</p>

<h2>Arquitectura</h2>
<pre><code>cache/
├── store.py      # MessageStore – Persistencia SQLite
├── queue.py      # MessageQueue – Lógica de cola y reintentos
├── mixin.py      # MessageQueueMixin – Integración con el cliente
└── __init__.py</code></pre>

<h2>1. MessageStore</h2>
<p>Almacenamiento persistente que maneja las operaciones CRUD de mensajes en SQLite.</p>

<h3>Estados de Mensaje (<code>MessageStatus</code>)</h3>
<table>
    <thead>
        <tr><th>Estado</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>PENDING</code></td><td>Esperando envío.</td></tr>
        <tr><td><code>SENT</code></td><td>Enviado al servidor.</td></tr>
        <tr><td><code>DELIVERED</code></td><td>Entregado al destinatario.</td></tr>
        <tr><td><code>READ</code></td><td>Leído por el destinatario.</td></tr>
        <tr><td><code>FAILED</code></td><td>Falló permanentemente.</td></tr>
        <tr><td><code>CANCELLED</code></td><td>Cancelado por usuario.</td></tr>
    </tbody>
</table>

<h3>Modelo de Datos (<code>Message</code>)</h3>
<pre><code class="language-python">@dataclass
class Message:
    msg_id: str
    to: str               # JID destino
    body: str
    msg_type: str = "text"
    status: MessageStatus = MessageStatus.PENDING
    created_at: float
    sent_at: Optional[float]
    delivered_at: Optional[float]
    read_at: Optional[float]
    retry_count: int = 0
    max_retries: int = 3
    last_error: str = ""
    metadata: dict = {}</code></pre>

<h3>Métodos de <code>MessageStore</code></h3>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>add(msg) -> bool</code></td><td>Guarda un mensaje.</td></tr>
        <tr><td><code>get(msg_id) -> Optional[Message]</code></td><td>Obtiene por ID.</td></tr>
        <tr><td><code>get_by_status(status, limit) -> List[Message]</code></td><td>Obtiene por estado.</td></tr>
        <tr><td><code>update_status(msg_id, new_status, error) -> bool</code></td><td>Actualiza estado.</td></tr>
        <tr><td><code>increment_retry(msg_id) -> bool</code></td><td>Incrementa contador de reintentos.</td></tr>
        <tr><td><code>delete(msg_id) -> bool</code></td><td>Elimina mensaje.</td></tr>
        <tr><td><code>get_stats() -> dict</code></td><td>Estadísticas de la BD.</td></tr>
        <tr><td><code>clear_old(days=30) -> int</code></td><td>Limpia mensajes antiguos (READ y DELIVERED).</td></tr>
    </tbody>
</table>

<h2>2. MessageQueue</h2>
<p>Gestiona la cola, los reintentos automáticos y los callbacks.</p>

<h3>Constructor</h3>
<pre><code class="language-python">MessageQueue(store: MessageStore, auto_retry: bool = True, max_backoff: float = 300)</code></pre>

<h3>Métodos Principales</h3>
<table>
    <thead>
        <tr><th>Método</th><th>Descripción</th></tr>
    </thead>
    <tbody>
        <tr><td><code>enqueue(msg_id, to, body, msg_type, metadata) -> Message</code></td><td>Añade a la cola.</td></tr>
        <tr><td><code>dequeue(status, limit) -> List[Message]</code></td><td>Obtiene mensajes para procesar.</td></tr>
        <tr><td><code>mark_sent(msg_id) -> bool</code></td><td>Marca como enviado.</td></tr>
        <tr><td><code>mark_delivered(msg_id) -> bool</code></td><td>Marca como entregado.</td></tr>
        <tr><td><code>mark_read(msg_id) -> bool</code></td><td>Marca como leído.</td></tr>
        <tr><td><code>mark_failed(msg_id, error) -> bool</code></td><td>Marca como fallido.</td></tr>
        <tr><td><code>start_auto_retry_worker()</code></td><td>Inicia worker de reintentos.</td></tr>
        <tr><td><code>stop_auto_retry_worker()</code></td><td>Detiene worker.</td></tr>
        <tr><td><code>register_callback(event, callback)</code></td><td>Registra callback.</td></tr>
        <tr><td><code>get_stats() -> dict</code></td><td>Estadísticas de la cola.</td></tr>
    </tbody>
</table>

<h3>Eventos Soportados</h3>
<ul>
    <li><code>on_message_sent</code></li>
    <li><code>on_message_delivered</code></li>
    <li><code>on_message_read</code></li>
    <li><code>on_message_failed</code></li>
</ul>

<h3>Backoff Exponencial con Jitter</h3>
<pre><code>Reintento 1: 1s   (±10% jitter)
Reintento 2: 2s
Reintento 3: 4s
...
Máximo: 300s (configurable)</code></pre>

<h2>3. MessageQueueMixin</h2>
<p>Mixin que integra la cola en <code>ToDusClient2</code> para crear <code>ToDusClientWithQueue</code>.</p>

<h3>Métodos Disponibles en el Cliente</h3>
<ul>
    <li><code>queue</code> (propiedad) – Acceso a <code>MessageQueue</code>.</li>
    <li><code>register_on_message_delivered(callback)</code></li>
    <li><code>register_on_message_read(callback)</code></li>
    <li><code>register_on_message_failed(callback)</code></li>
    <li><code>get_queue_stats() -> dict</code></li>
    <li><code>cleanup_queue()</code> – Limpia mensajes antiguos (&gt;30 días).</li>
</ul>

<h2>4. ToDusClientWithQueue</h2>
<p>Clase final que combina <code>ToDusClient2</code> y <code>MessageQueueMixin</code>, añadiendo el método <code>send_message_queued()</code>.</p>
<pre><code class="language-python">client = ToDusClientWithQueue(
    phone_number="5312345678",
    password="password",
    enable_queue=True,
    queue_db_path="~/.todus/messages.db"
)

# Envía y encola automáticamente
msg_id = client.send_message_queued("5387654321", "Mensaje con garantía")</code></pre>
<p><strong>Comportamiento Interno:</strong></p>
<ol>
    <li>Envía el mensaje inmediatamente usando <code>send_message()</code>.</li>
    <li>Lo agrega a la cola con estado <code>PENDING</code>.</li>
    <li>Si el envío es exitoso, lo marca como <code>SENT</code>.</li>
    <li>Si falla, el worker lo reintenta automáticamente según el backoff.</li>
    <li>Cuando se recibe la confirmación de entrega (<code>delivered</code> o <code>read</code>), se actualiza el estado y se disparan los callbacks.</li>
</ol>

<h2>Ejemplo Completo</h2>
<pre><code class="language-python">from todus import ToDusClientWithQueue

client = ToDusClientWithQueue("5312345678", "password", enable_queue=True)
client.login()

def on_delivered(msg):
    print(f"✅ Entregado: {msg.msg_id}")

def on_failed(msg):
    print(f"❌ Falló: {msg.msg_id} - {msg.last_error}")

client.register_on_message_delivered(on_delivered)
client.register_on_message_failed(on_failed)

for i in range(10):
    client.send_message_queued("5387654321", f"Mensaje {i}")

# Ver estadísticas
stats = client.get_queue_stats()
print(stats)</code></pre>

<h2>Base de Datos</h2>
<p>El esquema SQLite es el siguiente:</p>
<pre><code class="language-sql">CREATE TABLE messages (
    msg_id TEXT PRIMARY KEY,
    "to" TEXT NOT NULL,
    body TEXT NOT NULL,
    msg_type TEXT DEFAULT 'text',
    status TEXT DEFAULT 'pending',
    created_at REAL NOT NULL,
    sent_at REAL,
    delivered_at REAL,
    read_at REAL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX idx_status ON messages(status);
CREATE INDEX idx_to ON messages("to");
CREATE INDEX idx_created_at ON messages(created_at);</code></pre>
<p><strong>Ruta por defecto:</strong> <code>~/.todus/messages.db</code></p>