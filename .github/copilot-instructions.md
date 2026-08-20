**Overview**
- **Repo type:**: Cliente Python para ToDus (XMPP + HTTP) empaquetado como `todus`.
- **Python requirement:**: `>=3.11` (ver `pyproject.toml`).

**Arquitectura clave**
- **`todus/`**: paquete principal que exporta `ToDusClient`, `ToDusClient2`, `GroupClient` y utilidades (ver `todus/__init__.py`).
- **Transportes:**: XMPP socket + HTTP. Socket/XMPP está en `todus/client/base.py` (handshake, `_xmpp_session`) y la comunicación HTTP usa `requests` con `session`.
- **Parser/Events:**: `todus/parser.py` implementa `IncrementalParser` y funciones de parseo (`parse_todus_message`, `parse_presence`, `parse_iq`). Cambios en la forma de las stanzas deben preservar las claves del diccionario que retornan (p. ej. `id`, `from`, `body`, `raw`, `is_group`).
- **Builders/Helpers:**: los mensajes se construyen con funciones en `todus/stanza.py` y los mixins de funcionalidad (envío/recepción) viven en `todus/client/*.py` (p. ej. `message.py`).

**Patrones y convenciones del proyecto**
- **Dicts planos del parser:**: los parsers devuelven `dict` planos (no objetos). Respeta y no renombres keys cuando modifiques `parser.py` porque el resto del código (y tests) esperan keys concretas.
- **Context manager XMPP:**: usar `with self._xmpp_session(token) as sock:` para enviar datos. No reemplazar por cierre manual sin entender `_handshake` y `_process_handshake`.
- **Errores centralizados:**: clases de excepción en `todus/errors.py` (`TokenExpiredError`, `ConnectionLostError`, etc.) — lanzar estas clases, no genéricas, para que los callers las capturen correctamente.
- **Generación de IDs:**: usar `util.generate_token(...)` para `msg_id` y `mid` (visto en `todus/client/message.py`).
- **Logging:**: el logger principal es `todus` (ver `logging.getLogger('todus')`). Para debugging activo, configurar logging a `DEBUG` en pruebas manuales.

**Comandos útiles / flujo de desarrollo**
- **Instalación de desarrollo:**: `pip install -e .[dev]` (extras `dev` definido en `pyproject.toml`).
- **Ejecutar tests:**: este repo declara `pytest` pero la configuración en `pyproject.toml` apunta a `tests/`. En este repo la carpeta es `test/` — para ejecutar los tests locales usa:

```bash
python -m pytest -q test
```

- **Ejecutar un test individual:**: `python -m pytest -q test/test_stanzas.py::test_parse_message -k parse` (ajusta nombres según el archivo de test).
- **Depurar handshake XMPP:**: añadir `logging.basicConfig(level=logging.DEBUG)` en una sesión de reproducción o ejecutar con `PYTHONUNBUFFERED=1` y revisar logs del logger `todus`. Puntos relevantes: `todus/client/base.py` (`_handshake`, `_process_handshake`) y `todus/parser.py` (`IncrementalParser.feed`).

**Qué revisar antes de modificar código**
- Si vas a tocar `parser.py`, comprueba todos los tests en `test/test_stanzas.py` que validan keys del resultado.
- Si cambias la forma de construir stanzas, actualiza `todus/stanzas/` y busca usages en `todus/client/*` y `examples/bot.py`.

**Ejemplos rápidos (copy/paste)**
- Enviar mensaje de prueba (uso de API existente):

```python
from todus import ToDusClient
# crear cliente y usar mixins; revisar `examples/bot.py` para flujos completos
```

- Ejecutar parser incremental con chunk ejemplo:

```python
from todus.parser import IncrementalParser
parser = IncrementalParser()
chunks = ['<?xml...<m f="53...">', '</m>']
for c in chunks:
    stanzas = parser.feed(c)
    # cada item: dict con keys 'id','from','body','raw',...
```

**Archivos clave para revisar**
- `todus/parser.py` — parseo y `IncrementalParser`
- `todus/client/base.py` — conexión XMPP, handshake y `_xmpp_session`
- `todus/client/message.py` — ejemplos concretos de envío/recepción
- `todus/stanza.py` y `todus/stanzas/` — builders de stanzas
- `todus/errors.py`, `todus/util.py`, `todus/constants.py` — utilidades y constantes usadas ampliamente
- `pyproject.toml` — requisitos y extras (`dev`), revisar `pytest` config

Si algo de lo anterior no es correcto o quieres que añada ejemplos más concretos (p. ej. flows de autenticación, cómo reproducir problemas con proxy, o comandos para levantar un entorno de pruebas), dímelo y lo itero.

---
Por favor revisa este borrador y dime si quieres que añada: logs de ejemplo, pasos para reproducir fallos concretos (handshake/parseo/archivos), o snippets de `examples/bot.py` adaptados para debug.
