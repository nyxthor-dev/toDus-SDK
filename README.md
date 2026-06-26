<h1 align="center">📱 toDus-API</h1>

<p align="center">
  <a href="https://pypi.org/project/todus-sdk/"><img src="https://img.shields.io/pypi/v/todus-sdk" alt="PyPI"></a>
  <a href="https://pypi.org/project/todus-sdk/"><img src="https://img.shields.io/pypi/pyversions/todus-sdk" alt="Python"></a>
  <a href="https://vm1008079-web.github.io/toDus-API"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Docs"></a>
  <a href="https://github.com/vm1008079-web/toDus-API/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License"></a>
  <a href="https://github.com/vm1008079-web/toDus-API"><img src="https://img.shields.io/github/stars/vm1008079-web/toDus-API?style=social" alt="Stars"></a>
</p>

<p align="center"><strong>Cliente Python 🐍 para ToDus</strong> — la plataforma de mensajería instantánea cubana.</p>

<p align="center">
  <a href="https://vm1008079-web.github.io/toDus-API"><strong>📖 LEER LA DOCUMENTACIÓN COMPLETA 📖</strong></a>
</p>

---

## ✨ ¿Qué es toDus-API?

Es una librería moderna y poderosa para interactuar con la red de ToDus desde Python. Te permite crear:

- 🤖 **Bots inteligentes** - Responden a comandos y preguntas
- 📢 **Notificadores** - Envíos masivos con reintentos automáticos
- 💬 **Chat bots** - Integración con IA y LLMs
- 📊 **Sistemas de reportes** - Automatización de reportes
- 🔗 **Integraciones** - Sincroniza ToDus con tus sistemas

**Cobertura del protocolo:** ✅ 100% de las funciones de la app oficial

---

## 🚀 Instalación

```bash
pip install todus-sdk
```

---

## 🧪 Primeros Pasos

```python
from todus import ToDusClientWithQueue

# Crear cliente con cola persistente
client = ToDusClientWithQueue("5312345678", "tu_contraseña")
client.login()

# Enviar mensaje
msg_id = client.send_message_queued("5387654321", "¡Hola!")

# Escuchar mensajes
def on_message(msg):
    print(f"{msg.get('from')}: {msg.get('body')}")

client.listen_messages(client.token, on_message)
```

---

## 📚 Documentación Completa

| 📖 Tema | 📝 Descripción |
|--------|--------------|
| [🚀 Inicio Rápido](https://vm1008079-web.github.io/toDus-API/quickstart/) | Tutorial paso a paso |
| [🔐 Autenticación](https://vm1008079-web.github.io/toDus-API/authentication/) | SMS vs Contraseña |
| [💬 Mensajería](https://vm1008079-web.github.io/toDus-API/client/overview/) | API de mensajes |
| [👥 Grupos MUC](https://vm1008079-web.github.io/toDus-API/groups/) | Administración de grupos |
| [💾 Cola Persistente](https://vm1008079-web.github.io/toDus-API/cache/overview/) | Entrega garantizada |
| [🔧 Solución de Problemas](https://vm1008079-web.github.io/toDus-API/troubleshooting/) | Errores comunes |
| [💡 Ejemplos Avanzados](https://vm1008079-web.github.io/toDus-API/examples_advanced/) | Patrones reales |

---

## ⚡ Características

### 📱 Mensajería Completa
- Texto, imágenes, videos, stickers
- Ubicación, contactos, eventos
- Botones interactivos
- Ediciones y eliminaciones
- Confirmación de lectura

### 👥 Soporte para Grupos
- Unirse/Salir de grupos MUC Light
- Administración de miembros
- Roles (Owner, Moderator, Participant)
- Eventos de grupo (join, leave, kick)
- Enlaces de invitación

### 💾 Persistencia
- Cola de mensajes con SQLite
- Reintentos exponenciales automáticos
- Callbacks para eventos
- Estadísticas en tiempo real

### 🌐 Avanzado
- Canales públicos/privados
- Estados/Historias
- Proxies (HTTP, SOCKS4/5)
- Autenticación SMS
- Reconexión automática

---

## 💻 Casos de Uso

### 🤖 Bot con Comandos
```python
def on_message(msg):
    if msg.get('body', '').startswith('/'):
        cmd = msg['body'][1:]
        client.send_message_queued(
            msg['from'].split('@')[0],
            f"Ejecutaste: {cmd}"
        )

client.listen_messages(client.token, on_message)
```

### 📢 Newsletter
```python
phones = ["5351234567", "5387654321", "5362222222"]
for phone in phones:
    client.send_message_queued(phone, "📰 Última noticia: ...")
```

### 👥 Administrador de Grupo
```python
groups = client.groups
groups.join("id_grupo", nickname="AdminBot")
groups.send_message("id_grupo", "¡Hola grupo!")
members = groups.get_members("id_grupo")
```

Ver más ejemplos en [Ejemplos Avanzados](https://vm1008079-web.github.io/toDus-API/examples_advanced/)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Ver [guía de contribución](CONTRIBUTING.md).

**Pasos rápidos:**
1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/tu-feature`
3. Commit cambios: `git commit -am 'Añade feature'`
4. Push: `git push origin feature/tu-feature`
5. Abre Pull Request

---

## 📋 Requisitos

- **Python** >= 3.11
- **pip** (incluido en Python)

## ⚖️ Licencia

Este proyecto está bajo la licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.

---

## 👥 Contribuidores

Agradecemos a todos los que han contribuido:

- **OrionWolf** - Creador y mantenedor principal
- **Comunidad toDus** - Bug reports y sugerencias

¿Quieres aparecer aquí? ¡Contribuye!

---

## 📞 Soporte

- 📖 [Documentación](https://vm1008079-web.github.io/toDus-API/)
- 🐛 [Reportar bug](https://github.com/vm1008079-web/toDus-API/issues)
- 💬 [Discusiones](https://github.com/vm1008079-web/toDus-API/discussions)
- 📝 [CHANGELOG](CHANGELOG.md)

---

## 🔗 Enlaces

- 🌐 [Página de toDus](https://www.todus.cu)
- 📦 [PyPI Package](https://pypi.org/project/todus-sdk/)
- 📖 [Documentación](https://vm1008079-web.github.io/toDus-API/)
- 💻 [Repositorio GitHub](https://github.com/vm1008079-web/toDus-API)

---

<p align="center">
  Desarrollado con ❤️ por <strong>OrionWolf</strong><br>
  <em>Mantenido por la comunidad toDus</em>
</p>
