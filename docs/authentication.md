# 🔐 Autenticación

Esta guía cubre todos los métodos de autenticación con el SDK toDus.

## Métodos de Autenticación

El SDK soporta dos formas principales de autenticación:

### 1. Autenticación con Contraseña

La forma más simple y recomendada para bots y aplicaciones estables.

```python
from todus import ToDusClient2

client = ToDusClient2(
    phone_number="5312345678",
    password="tu_contraseña"
)

# Iniciar sesión
token = client.login()
print(f"Sesión iniciada. Token: {token[:20]}...")
```

**Ventajas:**
- ✅ Simple y rápido
- ✅ Seguro si usas HTTPS
- ✅ Ideal para bots permanentes

**Desventajas:**
- ❌ Requiere almacenar la contraseña
- ❌ Si se compromete, acceso total a la cuenta

---

### 2. Autenticación con Código SMS

Útil para aplicaciones móviles o cuando no tienes la contraseña disponible.

```python
from todus import ToDusClient

# Paso 1: Solicitar código
client = ToDusClient()
result = client.request_code(phone_number="5312345678")
print(f"Código enviado a: {result.get('phone_number')}")

# Paso 2: Validar el código recibido vía SMS
code = input("Ingresa el código SMS: ")
token = client.validate_code(phone_number="5312345678", code=code)
print(f"Autenticado. Token: {token[:20]}...")
```

**Flujo completo:**

```python
from todus import ToDusClient
from todus.errors import AuthenticationError

client = ToDusClient()
phone = "5312345678"

try:
    # Solicitar código
    print("Solicitando código SMS...")
    client.request_code(phone)
    
    # Esperar entrada del usuario
    code = input(f"Ingresa el código SMS enviado a +{phone}: ")
    
    # Validar código
    token = client.validate_code(phone, code)
    print("✅ Autenticación exitosa")
    
    # Ahora puedes usar el token para enviar mensajes
    msg_id = client.send_message(token, "5387654321@im.todus.cu", "Hola!")
    print(f"Mensaje enviado: {msg_id}")
    
except AuthenticationError as e:
    print(f"❌ Error de autenticación: {e}")
```

**Ventajas:**
- ✅ No requiere almacenar contraseña
- ✅ Más seguro para aplicaciones públicas
- ✅ Permite cambio de contraseña sin afectar

**Desventajas:**
- ❌ Requiere acceso a SMS
- ❌ Token tiene duración limitada
- ❌ Más pasos en el flujo

---

## Manejo de Tokens

El token es un JWT que expira después de cierto tiempo.

### Obtener el Token

```python
client = ToDusClient2("5312345678", "password")
token = client.login()  # Obtiene y almacena el token

# El token se guarda automáticamente
print(client.token)  # Acceder al token actual
```

### Token Expirado

Si el token expira, obtendrás un error:

```python
from todus.errors import TokenExpiredError

try:
    client.send_message("5387654321", "Hola")
except TokenExpiredError:
    print("Token expirado, reauthenticando...")
    client.login()  # Vuelve a autenticarse
    client.send_message("5387654321", "Hola")
```

### Decodificar Token

Para obtener información del token sin contactar el servidor:

```python
from todus.util import jwt_decode_payload

payload = jwt_decode_payload(token)
print(f"Usuario: {payload.get('username')}")
print(f"Expira en: {payload.get('exp')}")
```

---

## Buenas Prácticas de Seguridad

### ✅ Usa Variables de Entorno

Nunca hardcodees credenciales:

```python
import os
from dotenv import load_dotenv
from todus import ToDusClient2

load_dotenv()

phone = os.getenv("TODUS_PHONE")
password = os.getenv("TODUS_PASSWORD")

client = ToDusClient2(phone, password)
client.login()
```

**Archivo `.env`:**
```
TODUS_PHONE=5312345678
TODUS_PASSWORD=tu_contraseña_segura
```

### ✅ Guarda Credenciales de Forma Segura

Para aplicaciones que necesitan múltiples cuentas:

```python
import json
from cryptography.fernet import Fernet

# Generar clave (hazlo una sola vez)
# key = Fernet.generate_key()

cipher = Fernet(key)

credentials = {
    "phone": "5312345678",
    "password": "password123"
}

# Encriptar
encrypted = cipher.encrypt(json.dumps(credentials).encode())
with open("creds.enc", "wb") as f:
    f.write(encrypted)

# Desencriptar
with open("creds.enc", "rb") as f:
    encrypted = f.read()
decrypted = json.loads(cipher.decrypt(encrypted).decode())
print(decrypted)
```

### ✅ Manejo de Errores

```python
from todus.errors import AuthenticationError, TokenExpiredError

try:
    client.login()
except AuthenticationError as e:
    print(f"Credenciales inválidas: {e}")
    # No reintentar inmediatamente
except TokenExpiredError:
    print("Token expirado, reauthenticando...")
    client.login()
except Exception as e:
    print(f"Error inesperado: {e}")
```

---

## Estados de Autenticación

```python
# Verificar si está autenticado
if client.logged:
    print("Cliente autenticado")
    print(f"Usuario: {client.phone_number}")
    print(f"Token: {client.token[:20]}...")
else:
    print("Cliente no autenticado")
    client.login()
```

---

## Ejemplo: Bot con Reauthenticación Automática

```python
from todus import ToDusClientWithQueue
from todus.errors import TokenExpiredError
import time

class RobotPersistente:
    def __init__(self, phone, password):
        self.client = ToDusClientWithQueue(phone, password)
        self.client.login()
    
    def send_with_retry(self, to_phone, message, max_retries=3):
        for attempt in range(max_retries):
            try:
                return self.client.send_message_queued(to_phone, message)
            except TokenExpiredError:
                print(f"Token expirado, reauthenticando (intento {attempt+1}/{max_retries})")
                self.client.login()
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
    
    def listen_with_reconnect(self, callback):
        while True:
            try:
                self.client.listen_messages(self.client.token, callback)
            except Exception as e:
                print(f"Conexión perdida: {e}")
                print("Reauthenticando en 10 segundos...")
                time.sleep(10)
                self.client.login()

# Uso
bot = RobotPersistente("5312345678", "password")
bot.send_with_retry("5387654321", "Hola desde mi bot")
```

---

## Preguntas Frecuentes

**P: ¿Cuánto dura un token?**
R: Los tokens típicamente duran 24-48 horas. El SDK maneja automáticamente la reauthenticación.

**P: ¿Puedo usar el mismo token en múltiples dispositivos?**
R: Técnicamente sí, pero no es recomendado. Cada dispositivo debería autenticarse por separado.

**P: ¿Qué sucede si uso credenciales incorrectas?**
R: Se lanzará una `AuthenticationError`. No será posible recuperarse sin credenciales válidas.

**P: ¿Es seguro guardar el token en disco?**
R: No. Siempre encripta tokens almacenados. Es mejor volver a autenticarse cada vez.

**P: ¿Puedo revocar un token?**
R: Cambiando la contraseña se revocan todos los tokens activos.
