# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir a toDus-API! Esta guía te mostrará cómo hacerlo.

## Formas de Contribuir

- 🐛 **Reportar bugs** - Encontraste un problema
- 💡 **Sugerir features** - Tienes una idea nueva
- 📚 **Mejorar documentación** - Fixes en docs
- 🧪 **Escribir tests** - Aumentar cobertura
- 🔧 **Arreglar bugs** - Enviar PR
- ✨ **Implementar features** - Enviar PR

## Antes de Empezar

1. **Fork** el repositorio: https://github.com/vm1008079-web/toDus-API
2. **Clone** tu fork: `git clone https://github.com/tu-usuario/toDus-API.git`
3. **Crea una rama** para tu trabajo: `git checkout -b feature/mi-feature`

## Reporte de Bugs

Abre un [issue en GitHub](https://github.com/vm1008079-web/toDus-API/issues) con:

**Título:** Descripción breve del bug
```
Parser falla con stanzas XML vacías
```

**Descripción:**
```markdown
### Descripción
Cuando recibo una stanza vacía, el parser lanza KeyError.

### Pasos para reproducir
1. Conectar con cliente
2. Enviar stanza vacía: `<m/>`
3. Ver error

### Comportamiento esperado
El parser debería ignorar stanzas vacías o lanzar ParseError

### Comportamiento actual
Lanza `KeyError: 'id'` sin mensaje útil

### Entorno
- **OS:** Linux
- **Python:** 3.11
- **SDK Version:** 1.5.2

### Logs
```
Traceback (most recent call last):
  File "todus/parser.py", line 45, in parse_todus_message
    msg_id = stanza['id']
KeyError: 'id'
```
```

## Sugerencias de Features

Abre un [issue con la etiqueta `enhancement`](https://github.com/vm1008079-web/toDus-API/issues/new?labels=enhancement):

```markdown
### Descripción
Agregar soporte para reacciones emoji en mensajes

### Motivación
Muchas plataformas modernas soportan reacciones. Sería útil para bots interactivos.

### Ejemplo de uso
```python
client.add_reaction(msg_id, "👍")
client.remove_reaction(msg_id, "👍")
```

### Investigación
- Protocolo XMPP XEP-0444 define extensiones de reacciones
- ToDus podría usar stanzas `<r/>` con atributo `emoji`
```

## Desarrollo Local

### Setup

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/toDus-API.git
cd toDus-API

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e .[dev]
```

### Estructura del Proyecto

```
toDus-API/
├── todus/                 # Código principal
│   ├── client/            # Clases de cliente y mixins
│   ├── stanzas/           # Generadores XML
│   ├── cache/             # Sistema de cola
│   ├── parser.py          # Parser XMPP
│   ├── errors.py          # Excepciones
│   └── util.py            # Utilidades
├── tests/                 # Suite de tests
├── docs/                  # Documentación
├── examples/              # Ejemplos
└── pyproject.toml         # Configuración del proyecto
```

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest -v tests/

# Test específico
python -m pytest tests/test_parser.py::test_parse_message -v

# Con cobertura
pip install pytest-cov
pytest --cov=todus --cov-report=html
# Abre htmlcov/index.html
```

### Verificar Calidad de Código

```bash
# Linting
flake8 todus/ tests/ --max-line-length=120

# Type checking
pip install mypy
mypy todus/

# Formateo
pip install black
black todus/ tests/
```

## Crear un Pull Request

### Checklist antes de enviar

- ✅ Tu rama está basada en `main`
- ✅ Ejecutaste `pytest` localmente
- ✅ Agregaste tests para nuevas funciones
- ✅ Documentación actualizada si es necesario
- ✅ Mensaje de commit claro y descriptivo
- ✅ Sin cambios no relacionados

### Estructura del Commit

```bash
# Buen commit
git commit -m "fix: parser maneja stanzas vacías correctamente

- Añade validación en parse_todus_message()
- Lanza ParseError en lugar de KeyError
- Añade test para stanza vacía
- Refs #123"

# No tan bueno
git commit -m "fix stuff"
git commit -m "updated parser and other things"
```

### Enviar PR

1. **Push** a tu rama: `git push origin feature/mi-feature`
2. **Abre PR** en GitHub
3. **Rellena la plantilla:**

```markdown
## Descripción
Arregla el bug donde el parser falla con stanzas vacías

## Tipo de cambio
- [x] Bug fix
- [ ] Feature nueva
- [ ] Breaking change
- [ ] Documentación

## Testing
- [x] Agregué tests
- [x] Los tests pasan
- [x] Cobertura >= 80%

## Checklist
- [x] Mi código sigue el estilo del proyecto
- [x] Ejecuté pytest y pasó
- [x] Actualicé la documentación
- [x] No hay warnings/errores

## Screenshots (si aplica)
```

## Estándares de Código

### Convenciones de Nombres

```python
# Clases: PascalCase
class ToDusClient:
    pass

# Funciones y métodos: snake_case
def send_message(phone, body):
    pass

# Constantes: UPPER_CASE
XMPP_HOST = "im.todus.cu"

# Variables privadas: _leading_underscore
def _internal_method(self):
    pass
```

### Docstrings

Usar Google style docstrings:

```python
def send_message(self, to_phone: str, body: str, reply_to_id: str = "") -> str:
    """Envía un mensaje de texto.
    
    Envía un mensaje privado a través del protocolo XMPP.
    
    Args:
        to_phone: Número de teléfono del destinatario (formato 53XXXXXXXX)
        body: Texto del mensaje
        reply_to_id: ID del mensaje al que responder (opcional)
    
    Returns:
        El ID del mensaje enviado
    
    Raises:
        ConnectionLostError: Si la conexión XMPP se pierde
        TokenExpiredError: Si el token ha expirado
    
    Examples:
        >>> client = ToDusClient2("5312345678", "password")
        >>> client.login()
        >>> msg_id = client.send_message("5387654321", "¡Hola!")
    """
```

### Type Hints

Usar type hints en todas las funciones nuevas:

```python
from typing import Optional, List, Dict

def send_to_many(
    self,
    phones: List[str],
    message: str,
    delay: Optional[float] = None
) -> Dict[str, bool]:
    """Enviar a múltiples destinatarios."""
    pass
```

### Importes

Organizar como:
1. Librería estándar
2. Dependencias externas
3. Módulos locales

```python
import json
import logging
from typing import Optional

import requests
from pysocks import ProxyError

from todus.errors import ConnectionLostError
from todus.util import normalize_phone
```

## Actualizar Documentación

Editar archivos en `docs/`:

```bash
# Instalar mkdocs
pip install mkdocs-material

# Previsualizar
mkdocs serve  # Abre http://localhost:8000

# Compilar documentación
mkdocs build
```

**Estándares de documentación:**
- Usar Markdown con extensiones Material
- Ejemplos de código ejecutables
- Enlaces a referencias API
- Explicar el "por qué", no solo el "cómo"

## Versiones y Releases

### Numerar Versiones

Seguimos [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH` (e.g., `1.5.2`)
- **MAJOR**: Breaking changes
- **MINOR**: Features nuevas
- **PATCH**: Bug fixes

### Proceso de Release

1. Actualizar `todus/__init__.py`: `__version__`
2. Actualizar `CHANGELOG.md`
3. Crear tag en Git: `git tag v1.5.3`
4. Push: `git push origin main --tags`
5. GitHub Actions automáticamente publica a PyPI

## Comunicación

- 💬 **Discusiones:** [GitHub Discussions](https://github.com/vm1008079-web/toDus-API/discussions)
- 🐛 **Bugs:** [GitHub Issues](https://github.com/vm1008079-web/toDus-API/issues)
- 💬 **Chat:** Discord/Telegram (si existe comunidad)

## Código de Conducta

- Sé respetuoso y constructivo
- Acepta crítica constructiva
- Reporta comportamiento inapropiado

## Licencia

Al contribuir, aceptas que tu código esté bajo la licencia MIT.

---

**¡Gracias por contribuir! 🙏**
