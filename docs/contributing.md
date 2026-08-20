# Contribuir

## Formas de contribuir

- Reportar bugs
- Sugerir features
- Mejorar documentación
- Escribir tests
- Enviar PRs

## Setup local

```bash
git clone https://github.com/nyxthor-dev/toDus-API.git
cd toDus-API
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## Tests

```bash
# Todos
python -m pytest -v tests/

# Con cobertura
pytest --cov=todus --cov-report=html
```

## Linting

```bash
flake8 todus/ tests/ --max-line-length=120
```

## Estilo de código

- **Clases:** PascalCase
- **Funciones:** snake_case
- **Constantes:** UPPER_CASE
- **Docstrings:** Google style
- **Type hints** en todas las funciones nuevas

## Commits

```bash
git commit -m "fix: descripcion corta del cambio"
```

## Documentación

```bash
pip install mkdocs-material
mkdocs serve  # http://localhost:8000
```

## Pull Requests

1. Basar la rama en `main`
2. Ejecutar tests localmente
3. Actualizar documentación si aplica
4. Sin cambios no relacionados

## Licencia

Al contribuir, tu código queda bajo licencia MIT.