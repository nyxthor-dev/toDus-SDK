# Message Queue & History Manager

Sistema de cola de mensajes con persistencia local, auto-reintentos y callbacks de eventos.

## Características

- **Almacenamiento persistente**: SQLite con índices optimizados
- **Estados de mensaje**: pending, sent, delivered, read, failed, cancelled
- **Auto-retry**: Backoff exponencial configurable con jitter
- **Callbacks**: `on_message_sent`, `on_message_delivered`, `on_message_read`, `on_message_failed`
- **Thread-safe**: Uso de locks para acceso concurrente
- **Estadísticas**: Conteos por estado, worker status
- **Limpieza automática**: Remove mensajes antiguos (30+ días)

## Uso Básico

### Cliente con Queue Integrada

```python
from todus import ToDusClientWithQueue

client = ToDusClientWithQueue(
    phone_number="5312345678",
    password="mi_password",
    enable_queue=True,
    queue_db_path=None  # ~/.todus/messages.db por defecto
)

# Registrar callbacks
def on_delivered(msg):
    print(f"Entregado: {msg.msg_id}")

client.register_on_message_delivered(on_delivered)

# Enviar mensaje (se encolará automáticamente)
msg_id = client.send_message_queued("5387654321", "Hola")

# Ver estadísticas
stats = client.get_queue_stats()
print(stats)
```

### MessageQueue Standalone

```python
from todus.cache import MessageStore, MessageQueue

# Crear store y queue
store = MessageStore("/path/to/db.sqlite")
queue = MessageQueue(store, auto_retry=True)

# Enqueue
msg = queue.enqueue("msg1", "5312345678@im.todus.cu", "Hola")

# Marcar como enviado
queue.mark_sent("msg1")

# Marcar como entregado
queue.mark_delivered("msg1")

# Callbacks
queue.register_callback("on_message_delivered", lambda msg: print(f"Entregado: {msg.msg_id}"))

# Iniciar auto-retry worker
queue.start_auto_retry_worker()
```

## Estructura de BD

```sql
CREATE TABLE messages (
    msg_id TEXT PRIMARY KEY,
    to TEXT NOT NULL,
    body TEXT NOT NULL,
    msg_type TEXT DEFAULT 'text',
    status TEXT DEFAULT 'pending',  -- pending, sent, delivered, read, failed
    created_at REAL NOT NULL,
    sent_at REAL,
    delivered_at REAL,
    read_at REAL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}'
)
```

## Estados de Mensaje

| Estado | Descripción |
|--------|-------------|
| `pending` | Esperando envío |
| `sent` | Enviado al servidor |
| `delivered` | Entregado al destinatario |
| `read` | Leído por el destinatario |
| `failed` | Falló permanentemente |
| `cancelled` | Cancelado por usuario |

## Backoff Exponencial

```
Retry 1: 2^0 = 1s    (+ 0-10% jitter)
Retry 2: 2^1 = 2s    (+ 0-10% jitter)
Retry 3: 2^2 = 4s    (+ 0-10% jitter)
Max:     2^N capped a 300s (configurable)
```

## API Reference

### MessageStore

```python
store = MessageStore(db_path)
store.add(msg)                          # Agregar mensaje
store.get(msg_id)                       # Obtener por ID
store.get_by_status(status, limit)      # Obtener por estado
store.update_status(msg_id, new_status) # Actualizar estado
store.increment_retry(msg_id)           # Incrementar reintentos
store.delete(msg_id)                    # Eliminar
store.get_stats()                       # Estadísticas
store.clear_old(days=30)                # Limpiar antiguos
```

### MessageQueue

```python
queue = MessageQueue(store)
queue.enqueue(msg_id, to, body, msg_type, metadata)   # Encolar
queue.dequeue(status, limit)                           # Obtener por procesar
queue.mark_sent(msg_id)                                # Marcar enviado
queue.mark_delivered(msg_id)                           # Marcar entregado
queue.mark_read(msg_id)                                # Marcar leído
queue.mark_failed(msg_id, error)                       # Marcar fallido
queue.get_backoff_time(msg)                            # Calcular espera
queue.register_callback(event, callback)               # Registrar callback
queue.start_auto_retry_worker()                        # Iniciar worker
queue.stop_auto_retry_worker()                         # Detener worker
queue.get_stats()                                      # Estadísticas
```

## Ejemplos

Ver `/examples/offline_first_bot.py` para un ejemplo completo.

## Notas de Rendimiento

- **Índices**: Creados automáticamente en `status`, `to`, `created_at`
- **Thread-safety**: Locks RLock para operaciones concurrentes
- **Limpieza**: Ejecutar `cleanup_queue()` periódicamente
- **BD tamaño**: ~2KB por mensaje (incluyendo metadata)
