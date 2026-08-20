# Cola Persistente

Sistema de cola de mensajes con **SQLite**, reintentos automáticos con backoff exponencial y callbacks para seguimiento de estado.

Ideal para bots que necesitan garantizar la entrega en entornos con conectividad inestable.

## Arquitectura

```
cache/
├── store.py   # MessageStore – Persistencia SQLite
├── queue.py   # MessageQueue – Lógica de cola y reintentos
└── mixin.py   # Integración con el cliente
```

## Estados de mensaje

| Estado | Descripción |
|--------|-------------|
| `PENDING` | Esperando envío |
| `SENT` | Enviado al servidor |
| `DELIVERED` | Entregado al destinatario |
| `READ` | Leído por el destinatario |
| `FAILED` | Falló permanentemente |
| `CANCELLED` | Cancelado por el usuario |

## Modelo de datos

```python
@dataclass
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
    metadata: dict = {}
```

## MessageStore

Almacenamiento SQLite con operaciones CRUD.

| Método | Descripción |
|--------|-------------|
| `add(msg) -> bool` | Guarda un mensaje |
| `get(msg_id) -> Message` | Obtiene por ID |
| `get_by_status(status, limit) -> list` | Filtra por estado |
| `update_status(msg_id, status, error) -> bool` | Actualiza estado |
| `increment_retry(msg_id) -> bool` | Incrementa reintentos |
| `delete(msg_id) -> bool` | Elimina mensaje |
| `get_stats() -> dict` | Estadísticas |
| `clear_old(days=30) -> int` | Limpia mensajes antiguos |

## MessageQueue

Gestiona la cola, reintentos y callbacks.

```python
MessageQueue(store, auto_retry=True, max_backoff=300)
```

| Método | Descripción |
|--------|-------------|
| `enqueue(msg_id, to, body, msg_type, metadata) -> Message` | Añade a la cola |
| `dequeue(status, limit) -> list` | Obtiene mensajes para procesar |
| `mark_sent(msg_id) -> bool` | Marca como enviado |
| `mark_delivered(msg_id) -> bool` | Marca como entregado |
| `mark_read(msg_id) -> bool` | Marca como leído |
| `mark_failed(msg_id, error) -> bool` | Marca como fallido |
| `start_auto_retry_worker()` | Inicia worker de reintentos |
| `stop_auto_retry_worker()` | Detiene worker |
| `register_callback(event, callback)` | Registra callback |

**Backoff exponencial:** 1s, 2s, 4s... hasta 300s máximo.

## Ejemplo

```python
from todus import ToDusClientWithQueue

client = ToDusClientWithQueue("5312345678", "password", enable_queue=True)
client.login()

client.register_on_message_delivered(lambda m: print(f"Entregado: {m.msg_id}"))
client.register_on_message_failed(lambda m: print(f"Falló: {m.last_error}"))

for i in range(10):
    client.send_message_queued("5387654321", f"Mensaje {i}")

print(client.get_queue_stats())
```
