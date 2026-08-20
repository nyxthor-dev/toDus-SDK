# ToDus SDK para Python

Biblioteca Python para interactuar con **ToDus**, la plataforma de mensajería instantánea cubana. Implementa los protocolos XMPP y HTTP con una API simple y directa.

## Características

- **Mensajería completa** — texto, imágenes, videos, stickers, ubicaciones, contactos y eventos
- **Grupos MUC Light** — administración de miembros, roles, invitaciones
- **Cola persistente** — SQLite con reintentos automáticos y backoff exponencial
- **Canales** — públicos y privados con suscripción
- **Estados/Historias** — publicación y seguimiento
- **Event Bus** — sistema de eventos con filtros y prioridades
- **Rate limiter** — integrado, configurable por operación
- **Proxies** — HTTP y SOCKS4/5

## Instalación

```bash
pip install todus-sdk
```

## Ejemplo rápido

```python
from todus import ToDusClient2

client = ToDusClient2(phone_number="5312345678", password="tu_contraseña")
client.login()

client.send_message("5387654321", "Hola desde ToDus SDK")

def on_msg(msg):
    print(f"{msg.get('from')}: {msg.get('body')}")

client.listen_messages(on_msg)
```

## Documentación

| Guía | Descripción |
|------|-------------|
| [Instalación](installation.md) | Requisitos y métodos de instalación |
| [Inicio Rápido](quickstart.md) | Primeros pasos con el SDK |
| [Cliente](client/overview.md) | Arquitectura y clases principales |
| [Grupos](groups.md) | Manejo de grupos MUC Light |
| [Autenticación](authentication.md) | Contraseña y código SMS |
| [Event Bus](events/overview.md) | Sistema de eventos y filtros |
| [Cola Persistente](cache/overview.md) | Entrega garantizada con SQLite |
| [Ejemplos](examples_advanced.md) | Patrones de uso avanzados |
| [Solución de Problemas](troubleshooting.md) | Errores comunes y soluciones |
