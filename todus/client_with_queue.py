"""Cliente extendido con Message Queue integrado."""

from todus.client import ToDusClient2
from todus.cache import MessageQueueMixin, MessageStatus


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
        """Envía mensaje con soporte de queue.

        Orden correcto para no perder mensajes en fallo:

        1. Generar ``msg_id`` y encolar como PENDING **antes** de enviar.
        2. Intentar enviar pasando ese mismo ``msg_id`` para que el mensaje
           XMPP y la entrada de la cola usen el mismo ID (los receipts casan).
        3. Marcar como SENT si tuvo éxito, o dejar como PENDING (con retry
           automático del worker) si falló por red. Si la excepción no es
           recuperable (token inválido), se marca FAILED inmediatamente.

        Antes, si ``super().send_message()`` lanzaba una excepción, el mensaje
        nunca se encolaba y se perdía sin posibilidad de reintentar.
        """
        from .errors import AuthenticationError, TokenExpiredError
        from . import util as _util

        # 1. Pre-generar msg_id Y encolar ANTES de enviar.
        msg_id = _util.generate_msg_id()
        to_jid = _util.build_jid(to_phone) if not self._is_group_target(to_phone) else to_phone
        self._enqueue_message(to_jid, body, msg_id, msg_type="text",
                              reply_to_id=reply_to_id, to_phone=to_phone)

        # 2. Intentar enviar usando el mismo msg_id.
        try:
            super().send_message(to_phone, body, reply_to_id, msg_id=msg_id)
        except (TokenExpiredError, AuthenticationError):
            # Errores no recuperables: marcar como FAILED permanente inmediatamente.
            # NO usar ``mark_failed`` porque agendaría un retry que volvería a fallar.
            if self._message_queue:
                self._message_queue.store.update_status(
                    msg_id, MessageStatus.FAILED, error="auth_error"
                )
            raise
        except Exception as e:
            # Error de red/conexión: dejar como PENDING para que el worker reintente.
            # No relanzar para no romper flujos de envío masivo; el callback
            # ``register_on_message_failed`` notificará si finalmente falla.
            import logging
            logging.getLogger("todus").warning(
                "send_message_queued: envío falló para %s (%s). Queda en cola para retry.",
                msg_id, e,
            )
            return msg_id

        # 3. Marcar como enviado.
        self._mark_message_sent(msg_id)
        return msg_id

    def close(self) -> None:
        """Cierra recursos del cliente de forma determinista.

        Detiene el worker de auto-retry de la cola si está activo.
        A diferencia de ``__del__``, este método es seguro de llamar
        explícitamente y se recomienda hacerlo al finalizar el uso del cliente.
        """
        try:
            if getattr(self, "_queue_enabled", False) and getattr(self, "_message_queue", None):
                self._message_queue.stop_auto_retry_worker()
        except Exception:
            pass

    def __enter__(self) -> "ToDusClientWithQueue":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self):
        """Limpia recursos al destruir (fallback si no se llama ``close()``).

        Preferible llamar ``close()`` explícitamente o usar ``with``.
        Nunca propaga excepciones.
        """
        try:
            self.close()
        except Exception:
            pass
