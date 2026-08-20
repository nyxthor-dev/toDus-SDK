# Event Bus y Sistema de Filtros

## Introducción

El **EventBus** es un sistema centralizado de eventos que permite suscribirse a diferentes tipos de eventos (mensajes, presencia, recibos, etc.) con **filtros avanzados** y **prioridades**.

Ventajas:
- ✅ **Código reactivo y limpio**: Usa decoradores `@client.events.on(...)`
- ✅ **Filtros declarativos**: Filtra por remitente, contenido, tipo, regex, etc.
- ✅ **Prioridades**: Controla el orden de ejecución de handlers
- ✅ **Thread-safe**: Seguro para uso concurrente
- ✅ **Stop propagation**: Detén el flujo si es necesario

## Eventos Disponibles

El cliente despacha automáticamente estos eventos:

| Evento | Disparador | Ejemplo |
|--------|-----------|---------|
| `message` | Mensaje de texto, multimedia, chat state o deleted | Texto, imagen, video, ubicación |
| `presence` | Status de disponibilidad de usuario | Online, offline, away |
| `receipt` | Confirmación de entrega o lectura | Delivered, read |
| `iq` | Queries XMPP (canales, perfiles, etc.) | Response de petición |
| `tdack` | Acknowledgement de ToDus | Server confirmó recepción |
| `deleted` | Mensaje eliminado | Usuario borró un mensaje |
| `chat_state` | Estado de escritura | Escribiendo, pausado |
| `*` | **Wildcard**: todos los eventos | Captura todo |

## Uso Básico

### 1. Suscribirse a un evento simple

```python
from todus import ToDusClient

client = ToDusClient2(phone_number="5312345678", password="token")

@client.events.on("message")
def handle_message(event):
    print(f"Mensaje de {event['from']}: {event['body']}")

# Inicia la escucha
client.listen_messages(callback=lambda e: None)
```

### 2. Filtrar por remitente

```python
@client.events.on("message", from_phone="5387654321")
def handle_from_friend(event):
    print(f"Amigo dice: {event['body']}")
```

### 3. Filtrar por contenido (palabra clave)

```python
@client.events.on("message", contains_keyword="hola")
def handle_hello(event):
    print(f"Alguien saluda: {event['body']}")
```

### 4. Filtrar con expresiones regulares

```python
@client.events.on("message", regex=r"^\d{4}$")  # 4 dígitos
def handle_pin(event):
    print(f"PIN recibido: {event['body']}")
```

### 5. Filtro personalizado (función custom)

```python
def is_important(event):
    # eventos de grupos o con más de 10 caracteres
    return event.get("is_group") or len(event.get("body", "")) > 10

@client.events.on("message", custom=is_important)
def handle_important(event):
    print(f"Evento importante: {event['body']}")
```

### 6. Combinar múltiples filtros

```python
@client.events.on(
    "message",
    from_phone="5387654321",
    contains_keyword="urgente",
    priority=10  # mayor prioridad = ejecuta primero
)
def handle_urgent_from_friend(event):
    print("¡Amigo dice algo urgente!")
```

## Prioridades y Stop Propagation

### Ejecutar primero los handlers críticos

```python
@client.events.on("message", priority=100)  # se ejecuta primero
def critical_handler(event):
    print("1. Handler crítico")

@client.events.on("message", priority=50)
def normal_handler(event):
    print("2. Handler normal")

@client.events.on("message", priority=1)
def low_priority_handler(event):
    print("3. Handler baja prioridad")
```

### Detener la propagación

Si un handler devuelve `True`, se detiene la cadena de handlers:

```python
@client.events.on("message", priority=10)
def blocker(event):
    if event.get("body") == "spam":
        print("Bloqueado spam")
        return True  # ← detiene la propagación

@client.events.on("message", priority=1)
def never_runs_for_spam(event):
    # no se ejecuta si el mensaje es "spam"
    print("Este no corre si es spam")
```

## Manejo de Múltiples Eventos

### Suscribirse a todos los eventos (wildcard)

```python
@client.events.on("*")  # captura todo
def log_everything(event):
    event_type = event.get("_event_type")
    print(f"[{event_type}] {event}")
```

### Eventos específicos

```python
@client.events.on("receipt")
def on_receipt(event):
    msg_id = event.get("receipt")
    msg_type = event.get("receipt_type")  # "delivered" o "read"
    print(f"Mensaje {msg_id} {msg_type}")

@client.events.on("presence")
def on_presence(event):
    print(f"{event['from']} está {event.get('status', 'online')}")

@client.events.on("deleted")
def on_message_deleted(event):
    print(f"Mensaje {event['deleted']} fue eliminado")

@client.events.on("chat_state")
def on_chat_state(event):
    state = event.get("chat_state")  # "composing" o "paused"
    print(f"{event['from']} está {state}")
```

## API Completa

### `EventBus.subscribe()`

Registra un handler manualmente:

```python
def my_handler(event):
    print(event['body'])

# Crear filtro
from todus.events import build_filter
my_filter = build_filter(from_phone="5387654321")

# Suscribirse
client.events.subscribe(
    event_type="message",
    handler=my_handler,
    filters=my_filter,
    priority=5
)
```

### `EventBus.unsubscribe()`

Remover un handler:

```python
client.events.unsubscribe("message", my_handler)
```

### `EventBus.clear()`

Limpiar todos los handlers de un tipo, o todo:

```python
# Limpiar solo handlers de "message"
client.events.clear("message")

# Limpiar TODO
client.events.clear()
```

### `EventBus.dispatch()`

Despachar un evento manualmente (útil para testing):

```python
event = {"from": "5312345678", "body": "test"}
client.events.dispatch("message", event)
```

## Filtros Avanzados

### Opciones de `Filter`

```python
from todus.events import Filter

# Crear un filtro custom
my_filter = Filter(
    from_phone="5387654321",           # solo de este teléfono
    contains_keyword="pago",           # debe contener palabra
    msg_type="c",                      # tipo de mensaje
    is_group=False,                    # solo privado
    group_id=None,                     # o solo de este grupo
    regex=r"^\$\d+",                   # regex pattern
    custom=lambda e: True              # función personalizada
)

# Usar en decorador
@client.events.on("message", from_phone="5312345678", regex=r"test")
def handle_test(event):
    pass
```

### Crear filtro reutilizable

```python
from todus.events import build_filter

# Filtro para amigos que envían números
friend_filter = build_filter(
    from_phone="5387654321",
    regex=r"^\d+$"
)

# Usar en múltiples handlers
@client.events.on("message", priority=10)
def handler1(event):
    if friend_filter(event):
        print("Amigo envía números")

@client.events.on("message", priority=5)
def handler2(event):
    if friend_filter(event):
        print("Procesar número de amigo")
```

## Ejemplo Completo: Bot Inteligente

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="token")

# Handler de baja prioridad para logging
@client.events.on("*", priority=1)
def log_all_events(event):
    event_type = event.get("_event_type")
    print(f"[LOG] {event_type}: {event.get('from', '?')}")

# Handler crítico: filtrar spam
@client.events.on("message", priority=100, contains_keyword="spam")
def block_spam(event):
    print(f"🚫 Bloqueado spam de {event['from']}")
    return True  # detiene propagación

# Handler: responder a amigos
@client.events.on("message", from_phone="5387654321", priority=50)
def handle_friend_message(event):
    print(f"👋 Amigo dice: {event['body']}")
    # aquí podrías responder automáticamente

# Handler: procesar órdenes
@client.events.on("message", regex=r"^!help", priority=40)
def handle_commands(event):
    print(f"Comando recibido: {event['body']}")

# Handler: confirmar lectura en grupos
@client.events.on("message", is_group=True)
def auto_read_group_messages(event):
    print(f"Grupo: {event['body']}")

# Iniciar escucha
if __name__ == "__main__":
    try:
        client.login()
        print("Escuchando eventos...")
        client.listen_messages(callback=lambda e: None)
    except KeyboardInterrupt:
        print("Bot detenido")
```

## Mejores Prácticas

1. **Usa prioridades** para handlers críticos (bloqueo, validación)
2. **Usa filtros** para evitar procesar eventos innecesarios
3. **Devuelve `True`** desde handlers que quieres que detengan propagación
4. **Aprovecha wildcard `*`** para logging centralizado
5. **Thread-safe**: el EventBus maneja threads automáticamente
6. **Manejo de excepciones**: los errores en handlers se registran pero no rompen el bus

## Ver también

- [Referencia de Parser](../api/parser.md)
- [Tipos y Constantes](../api/types_constants.md)
- [Ejemplos Avanzados](../examples_advanced.md)
