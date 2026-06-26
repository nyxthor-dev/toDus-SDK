# 🌟 toDus SDK para Python

Bienvenido a la documentación oficial del **toDus SDK**, la biblioteca Python más completa para interactuar con **toDus**, la plataforma de mensajería instantánea cubana.

Este SDK implementa los protocolos **XMPP y HTTP** de toDus, ofreciendo una API moderna, fácil de usar y completamente asíncrona.

---

## ⚡ Características Destacadas

- 📱 Mensajería completa (texto, imágenes, videos, stickers, ubicación, contactos, eventos)
- 👥 Soporte para grupos MUC Light con administración de miembros
- 💾 Cola de mensajes persistente con SQLite y reintentos automáticos
- 🌐 Canales públicos/privados con suscripción
- 📸 Estados/Historias con seguimiento de usuarios
- 🔐 Autenticación con contraseña o código SMS
- 🔗 Soporte para proxies (HTTP, SOCKS4/5)
- ♻️ Reconexión automática y Keep-alive
- 📊 Callbacks para eventos y estadísticas en tiempo real

---

## 🚀 Inicio Rápido

### Instalación
```bash
pip install todus-sdk
```

### Tu primer bot
```python
from todus import ToDusClientWithQueue

# Crear cliente con cola persistente
client = ToDusClientWithQueue("5312345678", "tu_contraseña")
client.login()

# Enviar mensaje
msg_id = client.send_message_queued("5387654321", "¡Hola mundo!")

# Escuchar mensajes
def on_message(msg):
    sender = msg.get('from').split('@')[0]
    body = msg.get('body')
    print(f"📨 {sender}: {body}")

client.listen_messages(client.token, on_message)
```

---

## 📚 Documentación

| Sección | Descripción |
|---------|------------|
| [⚡ Inicio Rápido](quickstart.md) | Tutorial paso a paso |
| [🔐 Autenticación](authentication.md) | SMS vs Contraseña |
| [📝 Mensajería](client/overview.md) | API de mensajes |
| [👥 Grupos](groups.md) | Manejo de MUC Light |
| [💾 Cola Persistente](cache/overview.md) | Entrega garantizada |
| [🔧 Solución de Problemas](troubleshooting.md) | Errores comunes |
| [💡 Ejemplos Avanzados](examples_advanced.md) | Patrones reales |

---

## 🤝 Comunidad

- 🐛 [Reportar bugs](https://github.com/vm1008079-web/toDus-API/issues)
- 💬 [Discusiones](https://github.com/vm1008079-web/toDus-API/discussions)
- 🤝 [Contribuir](contributing.md)
- 📝 [CHANGELOG](changelog.md)

---

## ⚖️ Licencia

Este proyecto está bajo la licencia **MIT**. Puedes usarlo libremente.

**¡Feliz codificación! 🎉**
