"""Cliente extendido con Message Queue integrado."""

from todus.client import ToDusClient2
from todus.cache import MessageQueueMixin
from todus import util


class ToDusClientWithQueue(MessageQueueMixin, ToDusClient2):
    """Cliente ToDus con soporte de Message Queue integrado."""
    
    def __init__(self, phone_number: str, password: str = "", enable_queue: bool = True, 
                 queue_db_path: str = None, **kwargs):
        super().__init__(
            phone_number=phone_number,
            password=password,
            enable_queue=enable_queue,
            queue_db_path=queue_db_path,
            **kwargs
        )

    def send_message_queued(self, to_phone: str, body: str, reply_to_id: str = "") -> str:
        """Envía mensaje con soporte de queue."""
        msg_id = super().send_message(to_phone, body, reply_to_id)
        
        # Agregar a la cola
        to_jid = util.build_jid(to_phone) if not self._is_group_target(to_phone) else to_phone
        self._enqueue_message(to_jid, body, msg_id, msg_type="text", 
                            reply_to_id=reply_to_id, to_phone=to_phone)
        
        # Marcar como enviado en la cola
        self._mark_message_sent(msg_id)
        
        return msg_id

    def __del__(self):
        """Limpia recursos al destruir."""
        if self._queue_enabled and self._message_queue:
            self._message_queue.stop_auto_retry_worker()
