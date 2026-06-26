# 📦 Instalación

Guía completa para instalar el toDus SDK.

## Requisitos del Sistema

- **Python**: >= 3.11 (verificar con `python --version`)
- **pip**: Gestor de paquetes de Python (incluido en Python)
- **conexión a Internet**: Para descargar dependencias

## Instalación desde PyPI (Recomendado)

La forma más simple y recomendada:

```bash
pip install todus-sdk
```

Verificar que se instaló correctamente:

```bash
python -c "import todus; print(todus.__version__)"
# Output: 1.5.2
```

## Instalación desde Código Fuente (Desarrollo)

Para contribuir o usar la versión en desarrollo:

```bash
# Clonar el repositorio
git clone https://github.com/vm1008079-web/toDus-API.git
cd toDus-API

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e .[dev]
```

El flag `-e` instala en modo "editable", permitiéndote modificar el código y ver cambios inmediatamente.

## Dependencias

El SDK depende de las siguientes librerías (instaladas automáticamente):

| Librería | Propósito | Versión |
|----------|----------|---------|
| `requests` | Comunicación HTTP | >=2.28.0 |
| `pysocks` | Soporte para proxies SOCKS | >=1.7.1 |

Extras de desarrollo:

```bash
pip install -e .[dev]
```

Instala además:
- `pytest` >= 7.0.0 - Testing
- `build` - Empaquetado
- `twine` - Publicación en PyPI
- `mkdocs-material` >= 9.5.0 - Documentación
- `flake8` >= 6.0.0 - Linting

## Verificación de Instalación

Crea un script de prueba `test_install.py`:

```python
#!/usr/bin/env python3
"""Script para verificar la instalación de toDus SDK."""

import sys

def test_imports():
    """Verificar que los módulos se importan correctamente."""
    try:
        print("✓ Importando todus...", end=" ")
        import todus
        print(f"OK (v{todus.__version__})")
        
        print("✓ Importando cliente...", end=" ")
        from todus import ToDusClient2, ToDusClientWithQueue
        print("OK")
        
        print("✓ Importando tipos...", end=" ")
        from todus import FileType, ChatState, MessageType
        print("OK")
        
        print("✓ Importando errores...", end=" ")
        from todus.errors import ToDusError, TokenExpiredError
        print("OK")
        
        print("✓ Importando parser...", end=" ")
        from todus.parser import IncrementalParser
        print("OK")
        
        print("\n✅ Instalación verificada correctamente")
        return True
    except ImportError as e:
        print(f"\n❌ Error de importación: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
```

Ejecutar:
```bash
python test_install.py
```

## Instalación con Proxy

Si estás detrás de un proxy:

```bash
# HTTP
pip install --proxy [user:passwd@]proxy.server:port todus-sdk

# SOCKS5
pip install --proxy socks5://user:password@proxy:1080 todus-sdk
```

## Instalación en Entornos Específicos

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar toDus SDK
RUN pip install --no-cache-dir todus-sdk

COPY . .

CMD ["python", "main.py"]
```

Construir:
```bash
docker build -t todus-bot .
docker run todus-bot
```

### Raspberry Pi / ARM

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar con compilación de ruedas
pip install --only-binary :all: todus-sdk
```

### Windows

```bash
# PowerShell
python -m pip install todus-sdk

# O con cmd.exe
python -m pip install todus-sdk
```

### macOS

```bash
# Con Homebrew Python
brew install python3
pip install todus-sdk

# O con pyenv
pyenv install 3.11.0
pyenv local 3.11.0
pip install todus-sdk
```

### Linux (Debian/Ubuntu)

```bash
# Actualizar repositorios
sudo apt-get update

# Instalar Python 3.11 (si no está disponible)
sudo apt-get install python3.11 python3.11-venv

# Crear entorno virtual
python3.11 -m venv todus_env
source todus_env/bin/activate

# Instalar SDK
pip install todus-sdk
```

## Solución de Problemas de Instalación

### "ModuleNotFoundError: No module named 'todus'"

**Causa**: Python no encuentra el paquete instalado.

**Soluciones**:

```bash
# 1. Verificar que pip instala en el mismo Python
which python
which pip

# 2. Reinstalar
pip install --force-reinstall todus-sdk

# 3. Usar python -m pip
python -m pip install todus-sdk

# 4. Si usas entorno virtual, asegúrate de activarlo
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
```

### "ERROR: No matching distribution found"

**Causa**: Versión de Python no soportada o no disponible en PyPI.

**Soluciones**:

```bash
# Verificar versión de Python
python --version  # Debe ser >= 3.11

# Actualizar pip
pip install --upgrade pip

# Intenta instalación explícita de versión
pip install todus-sdk==1.5.2
```

### "ERROR: Could not find a version that satisfies"

**Causa**: Repositorio PyPI no accesible o conexión lenta.

**Soluciones**:

```bash
# Usar índice alternativo
pip install -i https://pypi.org/simple/ todus-sdk

# O instalar desde GitHub
pip install git+https://github.com/vm1008079-web/toDus-API.git
```

### "PermissionError: [Errno 13] Permission denied"

**Causa**: Intentas instalar sin permisos suficientes.

**Soluciones**:

```bash
# Opción 1: Usar flag --user (recomendado)
pip install --user todus-sdk

# Opción 2: Usar entorno virtual (mejor)
python -m venv myenv
source myenv/bin/activate
pip install todus-sdk

# Opción 3: sudo (no recomendado)
sudo pip install todus-sdk
```

### "SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]"

**Causa**: Problemas con certificados SSL/TLS.

**Soluciones**:

```bash
# Opción 1: Actualizar certificados
python -m certifi

# Opción 2: Desabilitar verificación (SOLO EN DESARROLLO)
pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org todus-sdk

# Opción 3: Usar proxy HTTPS
pip install -i https://mirror.example.com/simple todus-sdk
```

## Configuración Post-Instalación

### Crear archivo de configuración

```bash
mkdir -p ~/.todus
cat > ~/.todus/config.json << EOF
{
  "phone": "5312345678",
  "timeout": 15,
  "verify_ssl": false,
  "queue_db_path": "~/.todus/messages.db"
}
EOF
```

### Variable de entorno

```bash
# Linux/macOS
echo "export TODUS_PHONE='5312345678'" >> ~/.bashrc
echo "export TODUS_PASSWORD='tu_contraseña'" >> ~/.bashrc
source ~/.bashrc

# Windows PowerShell
[Environment]::SetEnvironmentVariable("TODUS_PHONE", "5312345678", "User")
[Environment]::SetEnvironmentVariable("TODUS_PASSWORD", "tu_contraseña", "User")
```

## Próximos Pasos

- 🚀 [Inicio Rápido](quickstart.md) - Primeros pasos
- 🔐 [Autenticación](authentication.md) - Configurar acceso
- 📚 [Documentación Completa](index.md) - Todas las guías

---

## Soporte

Si tienes problemas con la instalación:

1. 📖 Revisa la [guía de solución de problemas](troubleshooting.md)
2. 🐛 Abre un [issue en GitHub](https://github.com/vm1008079-web/toDus-API/issues)
3. 💬 Participa en [discussiones](https://github.com/vm1008079-web/toDus-API/discussions)