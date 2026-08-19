"""Mixin para integrar Message Queue en cliente ToDus."""

import logging
from typing import Callable, Optional, TYPE_CHECKING
from .store import MessageStore, MessageStatus
from .queue import MessageQueue

if TYPE_CHECKING:
    from ..client import ToDusClient2

logger = logging.getLogger("todus.cache.mixin")


class MessageQueueMixin:
    """Mixin para agregar Message Queue al cliente.

    Ahora incluye un `_send_fn` callable que el retry worker usa
    para reenviar mensajes pendientes automáticamente.
    """

    def __init__(self, *args, enable_queue: bool = True, queue_db_path: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue_enabled = enable_queue
        self._message_store: Optional[MessageStore] = None
        self._message_queue: Optional[MessageQueue] = None
        
        if self._queue_enabled:
            self._message_store = MessageStore(queue_db_path)
            self._message_queue = MessageQueue(self._message_store)
            self._message_queue.start_auto_retry_worker(send_fn=self._retry_send)

    @property
    def queue(self) -> Optional[MessageQueue]:
        """Acceso al message queue."""
        return self._message_queue

    def _enqueue_message(self, to: str, body: str, msg_id: str, msg_type: str = "text", **metadata):
        """Agrega mensaje a la cola (interno)."""
        if not self._queue_enabled or not self._message_queue:
            return
        self._message_queue.enqueue(msg_id, to, body, msg_type, metadata)

    def _mark_message_sent(self, msg_id: str):
        """Marca como enviado en la cola."""
        if not self._queue_enabled or not self._message_queue:
            return
        self._message_queue.mark_sent(msg_id)

    def _retry_send(self, msg) -> bool:
        """Reenvía un mensaje fallido. Usado por el auto-retry worker.
        
        Returns True si el reenvío fue exitoso.
        """
        try:
            if not self._token:
                return False
            metadata = msg.metadata or {}
            msg_type = msg.msg_type or "text"
            to = msg.to

            # Reconstruir el JID si es un teléfono (no grupo)
            from ..util import build_jid
            if "@" not in to and not self._is_group_target(to):
                to = build_jid(to)

            # Reenviar según el tipo de mensaje
            if msg_type == "text":
                reply_to_id = metadata.get("reply_to_id", "")
                super().send_message(self._token, to, msg.body, reply_to_id)
            else:
                # Para otros tipos, intentar como texto plano
                super().send_message(self._token, to, msg.body)
            return True
        except Exception as e:
            logger.error("Error reenviando mensaje %s: %s", msg.msg_id, e)
            return False

    def register_on_message_delivered(self, callback: Callable):
        """Registra callback cuando mensaje es entregado."""
        if self._message_queue:
            self._message_queue.register_callback("on_message_delivered", callback)

    def register_on_message_read(self, callback: Callable):
        """Registra callback cuando mensaje es leído."""
        if self._message_queue:
            self._message_queue.register_callback("on_message_read", callback)

    def register_on_message_failed(self, callback: Callable):
        """Registra callback cuando mensaje falla permanentemente."""
        if self._message_queue:
            self._message_queue.register_callback("on_message_failed", callback)

    def get_queue_stats(self) -> dict:
        """Obtiene estadísticas de la cola."""
        if self._message_queue:
            return self._message_queue.get_stats()
        return {}

    def cleanup_queue(self):
        """Limpia mensajes antiguos de la cola."""
        if self._message_store:
            deleted = self._message_store.clear_old(days=30)
            logger.info(f"Limpiados {deleted} mensajes antiguos")
