"""EventBus: dispatcher centralizado con filtros y prioridades.

Características principales:
- Registro por tipo de evento (string) y filtros declarativos.
- Decorador `on(event_type, **filters)` para registrar handlers.
- Prioridad (mayor valor = se ejecuta antes).
- Thread-safe (usa `threading.RLock`).
- Si un handler devuelve `True`, se detiene la propagación.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from .filters import build_filter

logger = logging.getLogger("todus")


HandlerEntry = Tuple[int, Callable[[Dict[str, Any]], Any], Callable[[Dict[str, Any]], bool]]


class EventBus:
    """Pequeño bus de eventos para toDus.

    Ejemplo:
        bus = EventBus()

        @bus.on('message', from_phone='53123')
        def handler(evt):
            print('mensaje:', evt['body'])

        bus.dispatch('message', {'from':'53123','body':'hola'})
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._handlers: Dict[str, List[HandlerEntry]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Any], *, filters: Optional[Callable[[Dict[str, Any]], bool]] = None, priority: int = 0) -> None:
        """Registra un handler para `event_type`.

        - `filters` es una función que recibe `event` y devuelve bool.
        - `priority` mayor -> se ejecuta antes.
        """
        filt = filters or (lambda e: True)
        with self._lock:
            self._handlers.setdefault(event_type, []).append((priority, handler, filt))
            # mantener ordenados por prioridad descendente
            self._handlers[event_type].sort(key=lambda x: x[0], reverse=True)
        logger.debug("Handler suscrito: %s priority=%s filters=%s", handler, priority, getattr(filters, '__name__', repr(filters)))

    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]) -> bool:
        """Remueve un handler y devuelve True si se eliminó."""
        with self._lock:
            entries = self._handlers.get(event_type, [])
            new_entries = [e for e in entries if e[1] is not handler]
            if len(new_entries) == len(entries):
                return False
            if new_entries:
                self._handlers[event_type] = new_entries
            else:
                self._handlers.pop(event_type, None)
            return True

    def clear(self, event_type: Optional[str] = None) -> None:
        """Remueve todos los handlers. Si `event_type` es None remueve todo."""
        with self._lock:
            if event_type is None:
                self._handlers.clear()
            else:
                self._handlers.pop(event_type, None)

    def on(self, event_type: str, priority: int = 0, **filter_kwargs):
        """Decorador para registrar handlers.

        Ejemplo:
            @bus.on('message', from_phone='53...', priority=5)
            def h(evt): ...
        """
        filt_fn = build_filter(**filter_kwargs) if filter_kwargs else None

        def decorator(fn: Callable[[Dict[str, Any]], Any]):
            self.subscribe(event_type, fn, filters=filt_fn, priority=priority)
            return fn

        return decorator

    def dispatch(self, event_type: str, event: Dict[str, Any], *, stop_on_true: bool = True) -> None:
        """Despacha un evento a los handlers registrados.

        - Si `stop_on_true` es True y un handler devuelve True, se detiene.
        """
        # Construir lista combinada de handlers: específicos + wildcard ('*')
        with self._lock:
            specific = list(self._handlers.get(event_type, []))
            wildcard = list(self._handlers.get("*", []))

        entries = specific + wildcard
        if not entries:
            logger.debug("No handlers for event %s", event_type)
            return

        # ordenar combinada por prioridad
        entries.sort(key=lambda x: x[0], reverse=True)

        # Enriquecer una copia del evento con el tipo real para handlers wildcard
        evt = dict(event) if isinstance(event, dict) else {"value": event}
        evt["_event_type"] = event_type

        for priority, handler, filt in entries:
            try:
                try:
                    if not filt(evt):
                        continue
                except Exception:
                    # si el filtro falla, no ejecutar el handler
                    logger.exception("Error evaluando filtro para handler %s", handler)
                    continue

                res = handler(evt)
                logger.debug("Handler %s ran for event %s (priority=%s) -> %s", handler, event_type, priority, res)
                if stop_on_true and res is True:
                    logger.debug("Propagation stopped by %s", handler)
                    break
            except Exception:
                logger.exception("Error en handler %s para evento %s", handler, event_type)
