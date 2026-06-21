"""Message Queue con auto-retry y backoff exponencial."""

import logging
import threading
import time
from typing import Callable, Optional, List
from .store import MessageStore, Message, MessageStatus

logger = logging.getLogger("todus.cache.queue")


class MessageQueue:
    """Cola de mensajes con reintentos automáticos."""

    def __init__(self, store: MessageStore, auto_retry: bool = True, max_backoff: float = 300):
        """
        Args:
            store: MessageStore para persistencia
            auto_retry: Si True, reintenta automáticamente mensajes fallidos
            max_backoff: Máximo tiempo de espera entre reintentos (segundos)
        """
        self.store = store
        self.auto_retry = auto_retry
        self.max_backoff = max_backoff
        self._running = False
        self._retry_thread = None
        self._callbacks = {
            "on_message_sent": [],
            "on_message_delivered": [],
            "on_message_read": [],
            "on_message_failed": [],
        }
        self._lock = threading.RLock()

    def enqueue(self, msg_id: str, to: str, body: str, msg_type: str = "text", metadata: dict = None) -> Message:
        """Agrega un mensaje a la cola."""
        msg = Message(
            msg_id=msg_id,
            to=to,
            body=body,
            msg_type=msg_type,
            status=MessageStatus.PENDING,
            metadata=metadata or {}
        )
        self.store.add(msg)
        logger.info(f"Mensaje encolado: {msg_id} -> {to}")
        return msg

    def dequeue(self, status: MessageStatus = MessageStatus.PENDING, limit: int = 10) -> List[Message]:
        """Obtiene mensajes por procesar."""
        return self.store.get_by_status(status, limit)

    def mark_sent(self, msg_id: str) -> bool:
        """Marca mensaje como enviado."""
        result = self.store.update_status(msg_id, MessageStatus.SENT)
        if result:
            msg = self.store.get(msg_id)
            self._trigger_callback("on_message_sent", msg)
        return result

    def mark_delivered(self, msg_id: str) -> bool:
        """Marca mensaje como entregado."""
        result = self.store.update_status(msg_id, MessageStatus.DELIVERED)
        if result:
            msg = self.store.get(msg_id)
            self._trigger_callback("on_message_delivered", msg)
        return result

    def mark_read(self, msg_id: str) -> bool:
        """Marca mensaje como leído."""
        result = self.store.update_status(msg_id, MessageStatus.READ)
        if result:
            msg = self.store.get(msg_id)
            self._trigger_callback("on_message_read", msg)
        return result

    def mark_failed(self, msg_id: str, error: str = "") -> bool:
        """Marca mensaje como fallido."""
        msg = self.store.get(msg_id)
        if msg and msg.retry_count < msg.max_retries:
            # Reintentar
            self.store.increment_retry(msg_id)
            return True
        else:
            # Fallido permanentemente
            result = self.store.update_status(msg_id, MessageStatus.FAILED, error)
            if result:
                self._trigger_callback("on_message_failed", msg)
            return result

    def get_backoff_time(self, msg: Message) -> float:
        """Calcula tiempo de espera para reintento (exponencial)."""
        base = 2 ** msg.retry_count
        backoff = min(base, self.max_backoff)
        # Añadir jitter (±10%)
        import random
        jitter = backoff * random.uniform(0.9, 1.1)
        return jitter

    def start_auto_retry_worker(self):
        """Inicia thread de reintentos automáticos."""
        if self._running:
            logger.warning("Auto-retry worker ya está corriendo")
            return

        self._running = True
        self._retry_thread = threading.Thread(target=self._retry_worker_loop, daemon=True)
        self._retry_thread.start()
        logger.info("Auto-retry worker iniciado")

    def stop_auto_retry_worker(self):
        """Detiene el thread de reintentos."""
        self._running = False
        if self._retry_thread:
            self._retry_thread.join(timeout=5)
        logger.info("Auto-retry worker detenido")

    def _retry_worker_loop(self):
        """Loop que procesa reintentos."""
        last_check = {}
        
        while self._running:
            try:
                # Obtener mensajes pending (potenciales para reintento)
                pending = self.dequeue(MessageStatus.PENDING, limit=100)
                
                for msg in pending:
                    now = time.time()
                    last_attempt = last_check.get(msg.msg_id, 0)
                    backoff = self.get_backoff_time(msg)
                    
                    # Si ha pasado suficiente tiempo, marcar para reintento
                    if now - last_attempt >= backoff:
                        logger.info(f"Listo para reintento: {msg.msg_id} (intento {msg.retry_count + 1}/{msg.max_retries})")
                        last_check[msg.msg_id] = now
                
                time.sleep(5)  # Chequear cada 5 segundos
            except Exception as e:
                logger.error(f"Error en retry worker: {e}")
                time.sleep(5)

    def register_callback(self, event: str, callback: Callable[[Message], None]):
        """Registra callback para evento."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _trigger_callback(self, event: str, msg: Message):
        """Ejecuta callbacks registrados."""
        if event in self._callbacks:
            for cb in self._callbacks[event]:
                try:
                    cb(msg)
                except Exception as e:
                    logger.error(f"Error en callback {event}: {e}")

    def get_pending_count(self) -> int:
        """Obtiene cantidad de mensajes pendientes."""
        pending = self.store.get_by_status(MessageStatus.PENDING)
        return len(pending)

    def get_failed_count(self) -> int:
        """Obtiene cantidad de mensajes fallidos."""
        failed = self.store.get_by_status(MessageStatus.FAILED)
        return len(failed)

    def get_stats(self) -> dict:
        """Obtiene estadísticas de la cola."""
        stats = self.store.get_stats()
        stats["total_pending"] = len(self.store.get_by_status(MessageStatus.PENDING))
        stats["total_failed"] = len(self.store.get_by_status(MessageStatus.FAILED))
        stats["worker_running"] = self._running
        return stats
