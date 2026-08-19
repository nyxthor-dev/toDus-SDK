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
    """
    
    def __init__(self, max_ops: int = 30, window_seconds: float = 60.0):
        self.max_ops = max_ops
        self.window = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
    
    def wait(self):
        """Bloquea hasta que sea seguro realizar la siguiente operación."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window
            
            # Limpiar timestamps fuera de la ventana
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            
            if len(self._timestamps) >= self.max_ops:
                # Calcular cuánto esperar hasta que el timestamp más viejo expire
                sleep_time = self._timestamps[0] + self.window - now + 0.1
                if sleep_time > 0:
                    logger.debug("Rate limit: esperando %.2fs", sleep_time)
            
        # Esperar fuera del lock para no bloquear otros threads
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        # Registrar esta operación
        with self._lock:
            self._timestamps.append(time.time())
    
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
