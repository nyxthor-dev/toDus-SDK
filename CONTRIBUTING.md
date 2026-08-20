# Contribuir a toDus-API

¡Gracias por tu interés en contribuir! 🎉

## Cómo Contribuir

### 1. Fork y Clone

```bash
git clone https://github.com/TU_USUARIO/toDus-API.git
cd toDus-API
```

### 2. Entorno de Desarrollo

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. Crear un Branch

```bash
git checkout -b feature/mi-nueva-funcionalidad
```

### 4. Hacer Cambios

- Escribe código limpio y legible
- Añade docstrings en español
- Incluye tests para funcionalidad nueva
- Mantén compatibilidad con Python >= 3.11

### 5. Ejecutar Tests

```bash
python -m pytest
```

### 6. Commit y Push

```bash
git add .
git commit -m "feat: descripción breve del cambio"
git push origin feature/mi-nueva-funcionalidad
```

### 7. Abrir un Pull Request

Ve a GitHub y abre un PR contra la rama `main`.

## Estilo de Código

- Seguimos PEP 8
- Docstrings en español
- Nombres de variables descriptivos
- Imports organizados: stdlib → third-party → local

## Convención de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — Nueva funcionalidad
- `fix:` — Corrección de bug
- `docs:` — Cambios en documentación
- `refactor:` — Reestructuración de código
- `test:` — Añadir o modificar tests
- `chore:` — Tareas de mantenimiento

## Reportar Bugs

Abre un [issue](https://github.com/ElJoker63/toDus-API/issues) con:

1. Descripción del problema
2. Pasos para reproducir
3. Comportamiento esperado vs actual
4. Versión de Python y SO

## Licencia

Al contribuir, aceptas que tus contribuciones se licenciarán bajo la [Licencia MIT](LICENSE).
