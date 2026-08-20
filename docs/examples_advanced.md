# 💡 Ejemplos Avanzados

Ejemplos completos y patrones recomendados para casos de uso avanzados.

## 0. Bot Reactivo con EventBus

Usa el **Event Bus** para código más limpio y reactivo:

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="token")

# Handler crítico: bloquear spam
@client.events.on("message", priority=100, contains_keyword="spam")
def block_spam(event):
    print(f"🚫 Bloqueado spam de {event['from']}")
    return True  # ← detiene propagación

# Handler: responder a amigos
@client.events.on("message", from_phone="5387654321", priority=50)
def handle_friend(event):
    print(f"👋 Amigo: {event['body']}")
    # responder automáticamente
    client.send_message("5387654321", "¡Hola!")

# Handler: procesar comandos
@client.events.on("message", regex=r"^!(\w+)", priority=40)
def handle_command(event):
    import re
    match = re.match(r"^!(\w+)", event['body'])
    if match:
        cmd = match.group(1)
        print(f"Comando: {cmd}")

# Handler: logging centralizado
@client.events.on("*", priority=1)  # wildcard
def log_everything(event):
    event_type = event.get("_event_type")
    sender = event.get("from", "?")
    print(f"[{event_type}] {sender}")

# Iniciar escucha
client.login()
print("🤖 Bot reactivo activo...")
client.listen_messages(callback=lambda e: None)
```

**Ventajas:**
- ✅ Código limpio con decoradores
- ✅ Prioridades automáticas
- ✅ Filtros declarativos
- ✅ Manejo centralizado de eventos

---

## 1. Bot Interactivo con Comandos

```python
from todus import ToDusClientWithQueue
from todus.errors import ConnectionLostError, TokenExpiredError
import re
import time

class CommandBot:
    """Bot que responde a comandos."""
    
    def __init__(self, phone, password):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.commands = {
            "help": self.cmd_help,
            "ping": self.cmd_ping,
            "status": self.cmd_status,
            "echo": self.cmd_echo,
        }
    
    def cmd_help(self, args):
        """Mostrar ayuda."""
        return "Comandos: help, ping, status, echo <text>"
    
    def cmd_ping(self, args):
        """Responder ping."""
        return "🏓 Pong!"
    
    def cmd_status(self, args):
        """Mostrar estado de la cola."""
        stats = self.client.get_queue_stats()
        return (
            f"📊 Estado de cola:\n"
            f"Pendientes: {stats['pending']}\n"
            f"Entregados: {stats['delivered']}\n"
            f"Fallidos: {stats['failed']}"
        )
    
    def cmd_echo(self, args):
        """Repetir mensaje."""
        if not args:
            return "Uso: echo <mensaje>"
        return " ".join(args)
    
    def process_command(self, msg):
        """Procesar comando del mensaje."""
        body = msg.get('body', '').strip()
        if not body.startswith('/'):
            return None
        
        # Parsear comando
        parts = body[1:].split()
        if not parts:
            return None
        
        cmd_name = parts[0].lower()
        cmd_args = parts[1:]
        
        if cmd_name not in self.commands:
            return f"❌ Comando desconocido: {cmd_name}"
        
        try:
            return self.commands[cmd_name](cmd_args)
        except Exception as e:
            return f"⚠️ Error: {str(e)}"
    
    def on_message(self, msg):
        """Procesar mensaje entrante."""
        if msg.get('is_group'):
            return  # Ignorar grupos
        
        sender = msg.get('from', '').split('@')[0]
        body = msg.get('body', '')
        
        # Procesar comando
        response = self.process_command(msg)
        if response:
            print(f"📤 Respondiendo a {sender}")
            self.client.send_message_queued(sender, response)
    
    def run(self):
        """Iniciar el bot."""
        print("🤖 Bot iniciado. Esperando mensajes...")
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.client.listen_messages(self.client.token, self.on_message)
            except (ConnectionLostError, TokenExpiredError) as e:
                retry_count += 1
                wait = min(2 ** retry_count, 60)
                print(f"⚠️ {type(e).__name__}. Reintentando en {wait}s...")
                time.sleep(wait)
                self.client.login()
            except KeyboardInterrupt:
                print("\n👋 Bot detenido")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                retry_count += 1
                time.sleep(5)

# Uso
if __name__ == "__main__":
    bot = CommandBot("5312345678", "password")
    bot.run()
```

---

## 2. Distribuidor de Mensajes (Newsletter)

```python
from todus import ToDusClientWithQueue
import json
from typing import List

class NewsletterBot:
    """Bot para enviar newsletters a múltiples usuarios."""
    
    def __init__(self, phone, password, contacts_file="contacts.json"):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.contacts = self.load_contacts(contacts_file)
    
    def load_contacts(self, file_path: str) -> List[str]:
        """Cargar lista de contactos."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Archivo {file_path} no encontrado")
            return []
    
    def save_contacts(self, file_path: str):
        """Guardar lista de contactos."""
        with open(file_path, 'w') as f:
            json.dump(self.contacts, f, indent=2)
    
    def add_contact(self, phone: str):
        """Agregar contacto."""
        from todus.util import normalize_phone
        phone = normalize_phone(phone)
        if phone not in self.contacts:
            self.contacts.append(phone)
            self.save_contacts("contacts.json")
    
    def send_newsletter(self, message: str, title: str = "📰 Newsletter"):
        """Enviar newsletter a todos."""
        print(f"📤 Enviando {title} a {len(self.contacts)} contactos...")
        
        successful = 0
        failed = 0
        
        full_message = f"{title}\n\n{message}"
        
        for phone in self.contacts:
            try:
                msg_id = self.client.send_message_queued(phone, full_message)
                successful += 1
                print(f"✅ {phone}: {msg_id}")
            except Exception as e:
                failed += 1
                print(f"❌ {phone}: {e}")
        
        print(f"\n📊 Resultados: {successful} exitosos, {failed} fallidos")
        return {"successful": successful, "failed": failed}
    
    def send_with_delay(self, message: str, delay_seconds: int = 5):
        """Enviar con retraso entre mensajes."""
        import time
        print(f"📤 Enviando con retraso de {delay_seconds}s entre mensajes...")
        
        for i, phone in enumerate(self.contacts, 1):
            try:
                self.client.send_message_queued(phone, message)
                print(f"{i}/{len(self.contacts)} ✅ {phone}")
                if i < len(self.contacts):
                    time.sleep(delay_seconds)
            except Exception as e:
                print(f"{i}/{len(self.contacts)} ❌ {phone}: {e}")

# Uso
if __name__ == "__main__":
    bot = NewsletterBot("5312345678", "password")
    
    # Agregar contactos
    bot.add_contact("5351234567")
    bot.add_contact("5387654321")
    
    # Enviar newsletter simple
    bot.send_newsletter(
        message="Aquí va el contenido del newsletter",
        title="🔔 Noticia Importante"
    )
    
    # Enviar con retraso para evitar rate limiting
    # bot.send_with_delay("Mensaje importante", delay_seconds=3)
```

---

## 3. Monitoreo de Conversaciones

```python
from todus import ToDusClientWithQueue
from datetime import datetime
import json

class ConversationMonitor:
    """Registra y analiza conversaciones."""
    
    def __init__(self, phone, password):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.conversations = {}
    
    def log_message(self, msg):
        """Registrar mensaje en log."""
        sender = msg.get('from', 'unknown').split('@')[0]
        body = msg.get('body', '')
        msg_id = msg.get('id', 'unknown')
        timestamp = datetime.now().isoformat()
        
        if sender not in self.conversations:
            self.conversations[sender] = []
        
        self.conversations[sender].append({
            "timestamp": timestamp,
            "id": msg_id,
            "body": body,
            "type": msg.get('type', 'normal'),
            "is_group": msg.get('is_group', False),
        })
        
        print(f"📝 {sender}: {body[:50]}...")
    
    def get_stats(self, phone: str = None):
        """Obtener estadísticas."""
        if phone:
            msgs = self.conversations.get(phone, [])
            return {
                "contact": phone,
                "message_count": len(msgs),
                "first_message": msgs[0]['timestamp'] if msgs else None,
                "last_message": msgs[-1]['timestamp'] if msgs else None,
            }
        else:
            return {
                "total_contacts": len(self.conversations),
                "total_messages": sum(len(m) for m in self.conversations.values()),
                "contacts": list(self.conversations.keys()),
            }
    
    def export_conversations(self, file_path: str):
        """Exportar conversaciones a JSON."""
        with open(file_path, 'w') as f:
            json.dump(self.conversations, f, indent=2, ensure_ascii=False)
        print(f"✅ Conversaciones exportadas a {file_path}")
    
    def on_message(self, msg):
        """Procesar mensaje."""
        self.log_message(msg)
    
    def run(self):
        """Iniciar monitoreo."""
        print("👁️ Iniciando monitoreo de conversaciones...")
        self.client.listen_messages(self.client.token, self.on_message)

# Uso
if __name__ == "__main__":
    monitor = ConversationMonitor("5312345678", "password")
    
    # Mostrar estadísticas antes de iniciar
    print(monitor.get_stats())
    
    # Iniciar monitoreo
    # monitor.run()
    
    # Exportar resultados
    # monitor.export_conversations("conversations.json")
```

---

## 4. Sistema de Persistencia con Base de Datos

```python
from todus import ToDusClientWithQueue
import sqlite3
from datetime import datetime

class DatabasedBot:
    """Bot con persistencia en SQLite."""
    
    def __init__(self, phone, password, db_path="bot.db"):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crear tablas si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                from_phone TEXT,
                to_phone TEXT,
                body TEXT,
                timestamp TEXT,
                msg_id TEXT UNIQUE,
                direction TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                phone TEXT PRIMARY KEY,
                first_seen TEXT,
                last_seen TEXT,
                message_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_message(self, msg, direction="received"):
        """Guardar mensaje en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        from_phone = msg.get('from', '').split('@')[0]
        to_phone = msg.get('to', '').split('@')[0]
        body = msg.get('body', '')
        msg_id = msg.get('id')
        
        if not msg_id:
            return
        
        try:
            cursor.execute('''
                INSERT INTO messages 
                (from_phone, to_phone, body, timestamp, msg_id, direction)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (from_phone, to_phone, body, datetime.now().isoformat(), msg_id, direction))
            
            # Actualizar tabla de usuarios
            cursor.execute('''
                INSERT INTO users (phone, first_seen, last_seen, message_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(phone) DO UPDATE SET
                    last_seen = ?,
                    message_count = message_count + 1
            ''', (from_phone, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Mensaje duplicado
        finally:
            conn.close()
    
    def get_user_history(self, phone: str, limit: int = 10):
        """Obtener histórico de usuario."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE from_phone = ? OR to_phone = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (phone, phone, limit))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def on_message(self, msg):
        """Procesar y guardar mensaje."""
        self.save_message(msg)

# Uso
if __name__ == "__main__":
    bot = DatabasedBot("5312345678", "password")
    
    # Ver histórico
    # history = bot.get_user_history("5351234567", limit=5)
    # for record in history:
    #     print(record)
    
    # Iniciar escucha
    # bot.client.listen_messages(bot.client.token, bot.on_message)
```

---

## 5. Sincronización con Webhook

```python
from todus import ToDusClientWithQueue
import requests
import json

class WebhookSync:
    """Envía eventos a un webhook remoto."""
    
    def __init__(self, phone, password, webhook_url: str):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.webhook_url = webhook_url
    
    def send_to_webhook(self, event_type: str, data: dict):
        """Enviar evento a webhook."""
        payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            print(f"✅ Webhook: {response.status_code}")
        except Exception as e:
            print(f"❌ Webhook error: {e}")
    
    def on_message(self, msg):
        """Sincronizar mensaje con webhook."""
        self.send_to_webhook("message", {
            "from": msg.get('from'),
            "body": msg.get('body'),
            "timestamp": datetime.now().isoformat(),
        })

# Uso con servidor Flask
from flask import Flask, request

app = Flask(__name__)
bot = WebhookSync(
    "5312345678",
    "password",
    webhook_url="https://mi-servidor.com/webhook"
)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibir eventos del bot."""
    data = request.json
    print(f"Evento recibido: {data['event']}")
    return {'status': 'ok'}, 200

# Iniciar bot
# threading.Thread(
#     target=bot.client.listen_messages,
#     args=(bot.client.token, bot.on_message),
#     daemon=True
# ).start()

# app.run(port=5000)
```

---

## 6. Análisis de Sentimiento

```python
from todus import ToDusClientWithQueue
from textblob import TextBlob  # pip install textblob

class SentimentBot:
    """Analiza sentimiento de mensajes."""
    
    def __init__(self, phone, password):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
    
    def analyze_sentiment(self, text: str) -> dict:
        """Analizar sentimiento del texto."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 a 1
        subjectivity = blob.sentiment.subjectivity  # 0 a 1
        
        if polarity > 0.1:
            sentiment = "😊 Positivo"
        elif polarity < -0.1:
            sentiment = "😢 Negativo"
        else:
            sentiment = "😐 Neutral"
        
        return {
            "sentiment": sentiment,
            "polarity": polarity,
            "subjectivity": subjectivity,
        }
    
    def on_message(self, msg):
        """Analizar y responder."""
        body = msg.get('body', '')
        sender = msg.get('from', '').split('@')[0]
        
        result = self.analyze_sentiment(body)
        
        # Responder según sentimiento
        response = f"Detecté un mensaje {result['sentiment'].lower()}"
        
        print(f"📊 {sender}: {result}")
        self.client.send_message_queued(sender, response)

# Uso
if __name__ == "__main__":
    bot = SentimentBot("5312345678", "password")
    # bot.client.listen_messages(bot.client.token, bot.on_message)
```

---

## 7. Rate Limiting y Throttling

```python
from todus import ToDusClientWithQueue
import time
from collections import deque

class ThrottledBot:
    """Bot con control de rate limiting."""
    
    def __init__(self, phone, password, max_messages_per_minute=30):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
        self.max_per_minute = max_messages_per_minute
        self.message_times = deque(maxlen=max_messages_per_minute)
    
    def wait_if_needed(self):
        """Esperar si se alcanzó el límite de tasa."""
        if len(self.message_times) < self.max_per_minute:
            return
        
        oldest = self.message_times[0]
        elapsed = time.time() - oldest
        wait_time = 60 - elapsed
        
        if wait_time > 0:
            print(f"⏳ Esperando {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.message_times.clear()
    
    def send_throttled(self, phone: str, message: str):
        """Enviar con throttling."""
        self.wait_if_needed()
        self.message_times.append(time.time())
        return self.client.send_message_queued(phone, message)

# Uso
if __name__ == "__main__":
    bot = ThrottledBot("5312345678", "password", max_messages_per_minute=10)
    
    # Enviar muchos mensajes sin ser bloqueado
    for i in range(20):
        bot.send_throttled("5387654321", f"Mensaje {i+1}")
```

---

Más ejemplos disponibles en el repositorio: [toDus-API/examples](https://github.com/vm1008079-web/toDus-API/tree/main/examples)
