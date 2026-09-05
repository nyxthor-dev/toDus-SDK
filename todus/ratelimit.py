"""Rate limiter simple para proteger contra bans por spam."""

import time
import threading
import logging
from collections import deque

logger = logging.getLogger("todus.ratelimit")


class RateLimiter:
    """Rate limiter por ventana deslizante.

    Limita la cantidad de operaciones en una ventana de tiempo.
    Ejemplo: 30 mensajes por minuto.

    Args:
        max_ops: Máximo de operaciones permitidas en la ventana.
        window_seconds: Tamaño de la ventana en segundos.

    Uso:
        limiter = RateLimiter(max_ops=30, window_seconds=60)
        limiter.wait()  # Bloquea si es necesario
        client.send_message(...)

    Fix v1.9.1: race condition en ``wait()``. Antes, dos threads podían
    ambos leer el mismo ``sleep_time``, dormir, y ambos hacer append sin
    verificar que ya estaban sobre el límite otra vez. El resultado era
    que el limiter terminaba con más timestamps que ``max_ops``. Ahora
    el bloque de "calcular + dormir + append" es atómico dentro del lock,
    y el sleep se hace con ``Condition.wait(timeout)`` que libera el lock
    durante la espera.
    """

    def __init__(self, max_ops: int = 30, window_seconds: float = 60.0):
        self.max_ops = max_ops
        self.window = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        # Condition permite a los threads esperar a que se libere un slot
        # sin hacer sleep activo fuera del lock (que es donde estaba el race).
        self._cond = threading.Condition(self._lock)

    def wait(self):
        """Bloquea hasta que sea seguro realizar la siguiente operación.

        Implementación atómica: el cálculo del sleep_time, el sleep, y el
        append del timestamp ocurren dentro del mismo lock (Condition).
        Otros threads que llamen ``wait()`` se quedan esperando en
        ``Condition.wait()`` hasta que uno libera un slot.
        """
        with self._cond:
            while True:
                now = time.time()
                cutoff = now - self.window

                # Limpiar timestamps fuera de la ventana
                while self._timestamps and self._timestamps[0] < cutoff:
                    self._timestamps.popleft()
                    # Notificar a otros threads que quizá ya tienen slot libre.
                    self._cond.notify_all()

                if len(self._timestamps) < self.max_ops:
                    # Hay slot libre: registrar y salir.
                    self._timestamps.append(time.time())
                    return

                # No hay slot: esperar hasta que el más viejo expire.
                sleep_time = self._timestamps[0] + self.window - now + 0.001
                if sleep_time > 0:
                    logger.debug("Rate limit: esperando %.3fs", sleep_time)
                    # wait() libera el lock durante la espera, permite que
                    # otros threads entran y hacen su propia espera.
                    self._cond.wait(timeout=sleep_time)

    def try_acquire(self) -> bool:
        """Intenta adquirir un slot sin bloquear.

        Returns True si la operación puede proceder inmediatamente.
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_ops:
                return False

            self._timestamps.append(now)
            return True

    @property
    def available(self) -> int:
        """Operaciones disponibles restantes en la ventana actual."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            return max(0, self.max_ops - len(self._timestamps))

    def reset(self):
        """Limpia el historial de operaciones."""
        with self._lock:
            self._timestamps.clear()
            # Notificar a threads dormidos que pueden reintentar.
            self._cond.notify_all()
