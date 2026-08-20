# Ejemplos Avanzados

Patrones de uso para casos reales.

## Bot con comandos

```python
from todus import ToDusClientWithQueue
from todus.errors import ConnectionLostError, TokenExpiredError

class CommandBot:
    def __init__(self, phone, password):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.commands = {
            "help": lambda args: "Comandos: help, ping, status, echo <text>",
            "ping": lambda args: "Pong!",
            "status": self._status,
            "echo": lambda args: " ".join(args) if args else "Uso: echo <mensaje>",
        }

    def _status(self, args):
        s = self.client.get_queue_stats()
        return f"Pendientes: {s['pending']}, Entregados: {s['delivered']}, Fallidos: {s['failed']}"

    def on_message(self, msg):
        if msg.get('is_group'):
            return
        body = msg.get('body', '').strip()
        if not body.startswith('/'):
            return
        parts = body[1:].split()
        cmd = parts[0].lower()
        if cmd in self.commands:
            sender = msg.get('from', '').split('@')[0]
            response = self.commands[cmd](parts[1:])
            self.client.send_message_queued(sender, response)

    def run(self):
        try:
            self.client.listen_messages(self.on_message)
        except (ConnectionLostError, TokenExpiredError):
            self.client.login()
            self.run()
        except KeyboardInterrupt:
            pass

bot = CommandBot("5312345678", "password")
bot.run()
```

## Bot reactivo con Event Bus

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="password")

@client.events.on("message", priority=100, contains_keyword="spam")
def block_spam(event):
    return True  # detiene propagacion

@client.events.on("message", from_phone="5387654321", priority=50)
def handle_friend(event):
    client.send_message("5387654321", "Hola!")

@client.events.on("*", priority=1)
def log_all(event):
    print(f"[{event.get('_event_type')}] {event.get('from', '?')}")

client.login()
client.listen_messages(callback=lambda e: None)
```

## Newsletter con cola

```python
from todus import ToDusClientWithQueue
import json, time

class NewsletterBot:
    def __init__(self, phone, password, contacts_file="contacts.json"):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        with open(contacts_file) as f:
            self.contacts = json.load(f)

    def send(self, message, delay=3):
        for i, phone in enumerate(self.contacts, 1):
            self.client.send_message_queued(phone, message)
            print(f"{i}/{len(self.contacts)} {phone}")
            if i < len(self.contacts):
                time.sleep(delay)

bot = NewsletterBot("5312345678", "password")
bot.send("Noticia importante")
```

## Rate limiter integrado

```python
from todus import ToDusClient2

client = ToDusClient2("5312345678", "password")
client.login()

# Configurar: max 20 operaciones por 60 segundos
client.set_rate_limit(max_ops=20, window_seconds=60)

for i in range(25):
    try:
        client.send_message("5387654321", f"Mensaje {i}")
    except Exception as e:
        print(f"Mensaje {i} limitado: {e}")
```

Mas ejemplos en el [repositorio](https://github.com/nyxthor-dev/toDus-API/tree/main/examples).