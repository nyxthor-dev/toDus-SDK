# Autenticación

El SDK soporta dos métodos de autenticación.

## Con contraseña

Recomendado para bots y aplicaciones permanentes.

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="tu_contraseña")
token = client.login()
```

## Con código SMS

Para aplicaciones móviles o cuando no tienes la contraseña.

```python
from todus import ToDusClient
from todus.errors import AuthenticationError

client = ToDusClient()
phone = "5312345678"

client.request_code(phone)
code = input(f"Código SMS enviado a +{phone}: ")
token = client.validate_code(phone, code)
```

## Tokens

El token es un JWT que expira después de cierto tiempo. `login()` lo obtiene y lo almacena automáticamente en `client.token`.

### Reauthenticación

```python
from todus.errors import TokenExpiredError

try:
    client.send_message("5387654321", "Hola")
except TokenExpiredError:
    client.login()
    client.send_message("5387654321", "Hola")
```

### Decodificar token

```python
from todus.util import jwt_decode_payload

payload = jwt_decode_payload(client.token)
print(f"Expira en: {payload.get('exp')}")
```

## Seguridad

!!! warning "Nunca hardcodees credenciales"

    Usa variables de entorno:

    ```python
    import os
    from todus import ToDusClient2

    client = ToDusClient2(
        phone_number=os.getenv("TODUS_PHONE"),
        password=os.getenv("TODUS_PASSWORD")
    )
    ```

## Estado de autenticación

```python
if client.logged:
    print(f"Autenticado: {client.phone_number}")
else:
    client.login()
```

## Preguntas frecuentes

**¿Cuánto dura un token?** Típicamente 24-48 horas.

**¿Puedo usar el mismo token en varios dispositivos?** Técnicamente sí, pero no es recomendado.

**¿Qué pasa si las credenciales son incorrectas?** Se lanza `AuthenticationError`.

**¿Es seguro guardar el token en disco?** No. Encripta tokens almacenados o reautentícate cada vez.

**¿Cómo revoco un token?** Cambiando la contraseña se revocan todos los tokens activos.
