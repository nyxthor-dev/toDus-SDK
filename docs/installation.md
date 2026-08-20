# Instalación

## Requisitos

- Python >= 3.11
- pip (incluido en Python)

## Desde PyPI

```bash
pip install todus-sdk
```

Verificar:

```bash
python -c "import todus; print(todus.__version__)"
```

## Desde código fuente

```bash
git clone https://github.com/nyxthor-dev/toDus-API.git
cd toDus-API

python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## Dependencias

| Paquete | Propósito |
|---------|----------|
| `requests` | Comunicación HTTP |
| `pysocks` | Soporte para proxies SOCKS |

Extras de desarrollo (`pip install -e .[dev]`):

- `pytest` — Testing
- `mkdocs-material` — Documentación
- `flake8` — Linting
- `build` — Empaquetado

## Con proxy

```bash
pip install --proxy socks5://user:password@proxy:1080 todus-sdk
```

## Docker

```dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir todus-sdk
COPY . .
CMD ["python", "main.py"]
```

## Problemas comunes

### ModuleNotFoundError

```bash
# Usar python -m pip para asegurar el mismo interprete
python -m pip install todus-sdk
```

### SSL errors

```bash
pip install --upgrade pip
pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org todus-sdk
```

### Permission denied

```bash
# Usar entorno virtual en vez de sudo
python -m venv venv
source venv/bin/activate
pip install todus-sdk
```

## Siguiente paso

[Inicio Rápido](quickstart.md) — Primeros pasos con el SDK.
