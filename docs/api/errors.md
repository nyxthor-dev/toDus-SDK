# Errores

Todas las excepciones heredan de `ToDusError`.

## Jerarquía

```
ToDusError
├── AuthenticationError     # Credenciales inválidas
├── TokenExpiredError       # Token JWT expirado
├── ConnectionLostError     # Conexión XMPP perdida
├── MessageError            # Error al enviar/recibir mensaje
├── UploadError             # Error en subida/descarga
├── ParseError              # Error parseando stanza
├── RateLimitError          # Demasiadas peticiones
├── StanzaError             # Stanza malformada
└── GroupError              # Error con grupos MUC Light
```

## Uso

```python
from todus import ToDusClient2
from todus.errors import AuthenticationError, ConnectionLostError

try:
    client = ToDusClient2("5312345678", "password")
    client.login()
except AuthenticationError:
    print("Credenciales incorrectas")
except ConnectionLostError:
    print("Error de red")
except Exception as e:
    print(f"Error: {e}")
```

## Notas

- `listen_messages()` captura `ConnectionLostError` internamente y reintenta con backoff exponencial
- `RateLimitError` se lanza cuando se excede el límite configurado (por defecto 30 ops/60s)
- Para detener `listen_messages`, usa el `stop_event` o `KeyboardInterrupt`
