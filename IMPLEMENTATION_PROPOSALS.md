# 5 Propuestas de Mejora para toDus-API Client

## 1. **Message Queue & Message History Manager** ✅ IMPLEMENTADO
**Problema resuelto:** Actualmente no hay forma de gestionar historial local, cola de pendientes o reintentos inteligentes.

**Descripción:**
- Crear `MessageQueue` que almacene mensajes localmente (SQLite/JSON) con estados (pending, sent, failed, delivered, read).
- Auto-retry con backoff exponencial para mensajes fallidos.
- Sincronización con servidor al reconectar.
- Callback events: `on_message_delivered`, `on_message_read`, `on_message_failed`.

**Impacto:**
- Ideal para bots offline-first
- Debugging mejorado (saber qué mensajes fallaron y por qué)
- UX mejorada (feedback real)

**Ubicación:** `todus/cache/` con `MessageQueue`, `HistoryDB` clases.

**Archivos creados:**
- `todus/cache/store.py` - MessageStore con SQLite
- `todus/cache/queue.py` - MessageQueue con reintentos
- `todus/cache/mixin.py` - MessageQueueMixin para integración
- `todus/cache/__init__.py` - Exports
- `todus/client_with_queue.py` - Cliente extendido
- `tests/test_cache.py` - Tests completos
- `examples/offline_first_bot.py` - Ejemplo de uso

---

## 2. **Event Bus / Message Dispatcher con Filters**
**Problema resuelto:** Callbacks simple son limitados; no hay forma de filtrar por tipo, sender, grupo, regex de contenido, etc.

**Descripción:**
- Implementar `EventBus` que centralice todos los eventos (messages, presence, receipts, errors).
- Suscriptores pueden registrarse con `filters` (p. ej. `from_phone=...`, `contains_keyword=...`, `msg_type=...`).
- Decorators para handlers: `@client.on('message', from_phone='5312345678')`.
- Priority-based dispatcher (handlers críticos primero).

**Impacto:**
- Código más organizado y reactivo
- Fácil de debuguear (log de eventos centralizados)
- Escalable para múltiples handlers

**Ubicación:** `todus/events/bus.py`, `todus/events/filters.py`.

---

## 3. **Rate Limiter & Throttling Engine**
**Problema resuelto:** No hay control de rate limits; riesgo de throttling/ban del servidor.

**Descripción:**
- Rate limiter por endpoint (enviar mensaje, subir archivo, crear grupo).
- Token bucket algorithm con tiempos configurables.
- Auto-backoff cuando recibe 429 del servidor.
- Estadísticas: mensajes/minuto, picos de carga, estimación de tiempo para enviar N mensajes.

**Impacto:**
- Evita baneo del servidor
- Bots pueden operar en modo "seguro"
- Debugging de throttling

**Ubicación:** `todus/limits/rate_limiter.py`.

---

## 4. **Async/Await Support (asyncio)**
**Problema resuelto:** Cliente es síncrono; en apps grandes causa bloqueos.

**Descripción:**
- Crear `ToDusClientAsync` que envuelva operaciones I/O con `asyncio`.
- `async send_message()`, `async listen_messages()`, `async upload_file()`, etc.
- Mantener compatibilidad con cliente síncrono actual.
- Soporte para `asyncio.gather()` en bots multitarea.

**Impacto:**
- Ideal para aplicaciones web (FastAPI, Django async)
- Mejor performance en bots con múltiples flujos
- Próximo nivel de profesionalismo

**Ubicación:** `todus/async_client.py`, `todus/asyncio/`.

---

## 5. **Plugin System & Middleware Architecture**
**Problema resuelto:** Código de cliente es monolítico; extensiones requieren fork/patch.

**Descripción:**
- Sistema de plugins que permita:
  - Interceptar mensajes antes/después (middleware)
  - Agregar handlers globales (logging, metrics, encryption)
  - Auto-respuestas, filtros de spam, traducción automática
- Hooks: `on_message_received`, `on_message_sent`, `on_error`, `on_authenticated`, etc.
- Plugins declarativos en YAML/JSON.

**Impacto:**
- Comunidad puede extender sin modificar core
- Encapsulación de features (logging, metrics, seguridad como plugins)
- Fácil reutilización

**Ubicación:** `todus/plugins/`, `todus/middleware/`.

---

## Tabla Comparativa

| Propuesta | Complejidad | Impacto | Tiempo Est. | Prioridad |
|-----------|-------------|--------|-----------|-----------|
| 1. Message Queue | Media | Alto (offline-first) | 3-4 días | **Alta** |
| 2. Event Bus | Media | Alto (escalabilidad) | 2-3 días | **Alta** |
| 3. Rate Limiter | Media-Baja | Medio (seguridad) | 1-2 días | Media |
| 4. Async/Await | Alta | Muy Alto (performance) | 4-5 días | **Alta** |
| 5. Plugin System | Alta | Muy Alto (extensibilidad) | 3-4 días | Media |

---

## Recomendación de Roadmap

1. **Fase 1 (Corto plazo):** Rate Limiter (#3) + Event Bus (#2)
   - Rápido de implementar
   - Mejora inmediata en estabilidad y escalabilidad

2. **Fase 2 (Mediano plazo):** Message Queue (#1)
   - Crítico para bots offline-first
   - Mejora UX significativamente

3. **Fase 3 (Largo plazo):** Async/Await (#4) + Plugin System (#5)
   - Transforma el cliente en plataforma
   - Habilita integración con ecosistemas modernos (FastAPI, etc)

---

## Próximos Pasos

¿Cuál propuesta te interesa más para comenzar la implementación?
- Necesitas más detalles técnicos de alguna?
- Quieres combinar algunas ideas?
- Prefieres un enfoque híbrido?
