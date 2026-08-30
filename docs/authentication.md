# Autenticación

El SDK soporta **4 métodos** de autenticación.

## 1. Con contraseña

Recomendado para bots y aplicaciones permanentes.

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="tu_contraseña")
client.login()
```

`POST https://auth.todus.cu/v2/auth/token` con `phone` + `password` + `uuid(150)` + `version_code`. Retorna el JWT.

## 2. Con código SMS

Para aplicaciones móviles o cuando no tienes la contraseña.

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678")
client.request_code()                                # recibe SMS
code = input(f"Código SMS enviado a +{client.phone_number}: ")
client.validate_code(code)                            # obtiene password
client.login()                                        # obtiene JWT con el password
```

- `request_code` → `POST /v2/auth/users.reserve` con `phone` + `uuid(150)` → SMS al teléfono
- `validate_code` → `POST /v2/auth/users.register` con `phone` + `uuid(150)` + `code` → password/secret (96 hex chars)
- `login` → `POST /v2/auth/token` con `phone` + `password` + `uuid(150)` + `version_code` → JWT

## 3. Con token JWT

Si ya tienes un JWT (por ejemplo, almacenado de una sesión anterior), puedes setearlo directamente sin llamar a `login()`:

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678")
client._token = "eyJhbGc..."  # tu JWT previamente obtenido
# Ahora client.token está disponible y client.logged == True
```

## 4. Solo con número (login_with_phone_only)

!!! warning "Explota una debilidad del servidor"
    Este método aprovecha que el endpoint `/v2/auth/token` acepta como
    "password" cualquier UUID (con guiones removidos, primeros 32 chars)
    **sin validar contra el password real de la cuenta**. Permite
    autenticarse con solo el número de teléfono, sin SMS ni contraseña.

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678")
client.login_with_phone_only()  # sin password, sin SMS, sin JWT previo
```

### Procedimiento exacto

`POST https://auth.todus.cu/v2/auth/token`

Headers (difieren del login normal):

```
content-type: application/octet-stream
user-agent: ToDus 2.1.1
```

Payload (protobuf, dos campos wire-type 2):

```
sf(1, PHONE) + sf(2, SECRET)
```

Donde:

- `sf(n, v)` = `bytes([(n<<3)|2]) + varint(len(v)) + v.encode()`
- `PHONE` = teléfono cubano normalizado (10 dígitos, ej: `5312345678`)
- `UUID` (hardcodeado en el SDK): `fake-1234-5678-90ab-cdef12345678`
- `SECRET` = `UUID.replace('-', '')[:32]` = `fake1234567890abcdef12345678`

Respuesta: el body contiene el JWT (formato `eyJ...`), extraído con regex para
mayor robustez ante basura alrededor del token.

## Tokens

El token es un JWT que expira después de cierto tiempo. `login()` y
`login_with_phone_only()` lo obtienen y lo almacenan automáticamente en
`client.token`.

### Reauthenticación

```python
from todus.errors import TokenExpiredError

try:
    client.send_message("5387654321", "Hola")
except TokenExpiredError:
    client.login()  # o client.login_with_phone_only()
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
    client.login()  # o client.login_with_phone_only()
```

## Preguntas frecuentes

**¿Cuánto dura un token?** Típicamente 24-48 horas.

**¿Puedo usar el mismo token en varios dispositivos?** Técnicamente sí, pero no es recomendado.

**¿Qué pasa si las credenciales son incorrectas?** Se lanza `AuthenticationError`.

**¿Es seguro guardar el token en disco?** No. Encripta tokens almacenados o reautentícate cada vez.

**¿Cómo revoco un token?** Cambiando la contraseña se revocan todos los tokens activos.

**¿Es seguro `login_with_phone_only`?** No — explota una debilidad del servidor. Úsalo solo cuando
no tengas otra opción y eres consciente del riesgo.
