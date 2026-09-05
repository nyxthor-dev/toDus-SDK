import logging
import threading
import time
import socket
from typing import Callable
from .. import util, stanza, constants
from ..errors import TokenExpiredError, ConnectionLostError
from ..types import FileType

logger = logging.getLogger("todus")


class ToDusMessageMixin:
    """Mixin que contiene la lógica de mensajería (envío y recepción) de ToDus."""

    # --- Mensajeria Privada ---

    def send_message(self, token: str, to_jid: str, body: str, reply_to_id: str = "",
                     msg_id: str = "") -> str:
        """Envía mensaje de texto privado. Retorna el msg_id generado.

        Si se pasa ``msg_id`` explícito, se usa ese en lugar de generar uno nuevo
        (útil para que la cola persistente y el envío XMPP usen el mismo ID, de
        modo que los receipts casen).
        """
        self._rate_limiter.wait()
        mid = msg_id or util.generate_msg_id()
        msg = stanza.message(to_jid, body, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def edit_message(self, token: str, to_jid: str, new_body: str, original_msg_id: str, reply_to_id: str = "") -> str:
        """Edita un mensaje privado."""
        self._rate_limiter.wait()
        edit_id = util.generate_msg_id()
        msg = stanza.edit_message(to_jid, new_body, original_msg_id, edit_id=edit_id, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return edit_id

    def send_file_message(self, token: str, to_jid: str, url: str, file_type: FileType,
                          caption: str = "", file_name: str = "", file_size: int = 0,
                          reply_to_id: str = "") -> str:
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.file_message(to_jid, url, int(file_type), caption, msg_id=mid,
                                  file_name=file_name, file_size=file_size, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_image_message(self, token: str, to_jid: str, url: str, file_name: str,
                           file_size: int, width: int = 0, height: int = 0,
                           thumbnail: str = "", caption: str = "", reply_to_id: str = "") -> str:
        """Envía mensaje privado con imagen adjunta."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.image_message(to_jid, url, file_name, file_size, width, height,
                                   thumbnail, caption, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_image_message_simple(self, token: str, to_jid: str, url: str,
                                  file_name: str, file_size: int, msg_id: str = "",
                                  reply_to_id: str = "") -> str:
        """Envía mensaje privado con imagen SIN metadata."""
        self._rate_limiter.wait()
        mid = msg_id or util.generate_msg_id()
        msg = stanza.image_message_simple(to_jid, url, file_name, file_size,
                                          msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_button_message(self, token: str, to_jid: str, text: str, buttons: list[dict],
                            reply_to_id: str = "") -> str:
        """Envía mensaje con botones interactivos."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.button_message(to_jid, text, buttons, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_contact_message(self, token: str, to_jid: str, contact_id: str,
                             contact_name: str, contact_phone: str, reply_to_id: str = "") -> str:
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.contact_message(to_jid, contact_id, contact_name, contact_phone,
                                     msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_sticker_message(self, token: str, to_jid: str, sticker_id: str,
                             sticker_name: str, sticker_pack: str, sticker_hash: str,
                             reply_to_id: str = "") -> str:
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.sticker_message(to_jid, sticker_id, sticker_name, sticker_pack,
                                     sticker_hash, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_video_message(self, token: str, to_jid: str, url: str, video_id: str,
                           file_name: str, file_size: int, duration: int,
                           width: int, height: int, thumbnail: str,
                           info_text: str = "", reply_to_id: str = "") -> str:
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.video_message(to_jid, url, video_id, file_name, file_size,
                                   duration, width, height, thumbnail,
                                   msg_id=mid, info_text=info_text, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_voice_message(self, token: str, to_jid: str, url: str, file_name: str,
                           file_size: int, duration: int, wave_sample: str = "",
                           caption: str = "", reply_to_id: str = "") -> str:
        """Envía nota de voz (extensión voice:n).

        ``wave_sample`` es la forma de onda para dibujar la burbuja
        (amplitudes separadas por coma).
        """
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.voice_message(to_jid, url, file_name, file_size, duration,
                                   wave_sample, msg_id=mid, caption=caption,
                                   reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_gif_message(self, token: str, to_jid: str, url: str, file_name: str,
                         file_size: int, width: int = 0, height: int = 0,
                         thumbnail: str = "", caption: str = "", reply_to_id: str = "") -> str:
        """Envía GIF (extensión gif:n)."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.gif_message(to_jid, url, file_name, file_size, width, height,
                                 thumbnail, caption, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_stream_video_message(self, token: str, to_jid: str, guid: str,
                                  stream_url: str, duration: int = 0,
                                  extra_codec: str = "") -> str:
        """Envía video en stream (extensión streamvideo:n)."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.stream_video_message(to_jid, guid, stream_url, duration,
                                          extra_codec, msg_id=mid)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_reaction(self, token: str, to_jid: str, reacted_msg_id: str,
                      reaction_code: str) -> str:
        """Envía una reacción a un mensaje (extensión reaction:n)."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.reaction_message(to_jid, reacted_msg_id, reaction_code, msg_id=mid)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def forward_message(self, token: str, to_jid: str, original_msg_id: str,
                        original_owner: str = "", body: str = "") -> str:
        """Reenvía un mensaje (extensión resend:n)."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.forward_message(to_jid, original_msg_id, original_owner,
                                     msg_id=mid, body=body)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_call_signal(self, token: str, to_jid: str, call_state: str,
                         call_id: str) -> str:
        """Envía señalización de llamada (extensión tcall:n)."""
        # Fix v1.9.1: aplicar rate limiter — todos los demás send_* lo usan.
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.tcall_message(to_jid, call_state, call_id, msg_id=mid)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_location_message(self, token: str, to_jid: str, lat: float, lon: float,
                              zoom: float = 11.0, text: str = "", reply_to_id: str = "") -> str:
        """Envía un mensaje con ubicación adjunta."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.location_message(to_jid, lat, lon, zoom, text, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_event_message(self, token: str, to_jid: str, title: str, start: int,
                           end: int, all_day: bool, ics_data: str,
                           event_id: str = "", reply_to_id: str = "") -> str:
        """Envía un mensaje con evento/calendario adjunto."""
        self._rate_limiter.wait()
        mid = util.generate_msg_id()
        msg = stanza.event_message(to_jid, event_id, title, start, end, all_day,
                                   ics_data, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return mid

    def send_chat_state(self, token: str, to_jid: str, state: str) -> None:
        # Fix v1.9.1: aplicar rate limiter para evitar flood cuando el
        # cliente envía 'composing' por cada keystroke. Antes este método
        # no tenía rate limit y podía saturar el servidor.
        self._rate_limiter.wait()
        st = stanza.chat_state(to_jid, state)
        with self._xmpp_session(token) as sock:
            sock.sendall(st.encode())

    def delete_message(self, token: str, to_jid: str, message_id: str,
                       msg_type: str = "c", body: str = "", media_xml: str = "",
                       reply_to_id: str = "") -> str:
        """Elimina un mensaje propio."""
        self._rate_limiter.wait()
        msg = stanza.delete_message(to_jid, message_id, msg_id=message_id, msg_type=msg_type,
                                    body=body, media_xml=media_xml, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return message_id

    def send_read_receipt(self, token: str, to_jid: str, msg_id: str, msg_type: str = "c") -> str:
        """Envía confirmación de lectura (displayed, ``dd``)."""
        rid = util.generate_msg_id()
        msg = stanza.read_receipt(to_jid, msg_id, receipt_id=rid, msg_type=msg_type)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return rid

    def send_delivery_receipt(self, token: str, to_jid: str, msg_id: str, msg_type: str = "c") -> str:
        """Envía confirmación de entrega (received, ``rd``)."""
        rid = util.generate_msg_id()
        msg = stanza.receipt(to_jid, msg_id, receipt_id=rid, msg_type=msg_type)
        with self._xmpp_session(token) as sock:
            sock.sendall(msg.encode())
        return rid

    # --- Recepción de mensajes ---

    def listen_messages(self, token: str, callback: Callable[[dict], None],
                        stop_event: threading.Event = None, max_retries: int = 0,
                        base_backoff: float = 15.0, max_backoff: float = 300.0) -> None:
        """Escucha mensajes con soporte para detener gracefulfully y backoff exponencial.

        Args:
            token: Token de autenticación.
            callback: Función llamada por cada mensaje recibido.
            stop_event: threading.Event para detener el loop (opcional).
            max_retries: Máximo de reintentos de reconexión (0 = infinito).
            base_backoff: Tiempo base de espera entre reintentos (segundos).
            max_backoff: Tiempo máximo de espera entre reintentos (segundos).
        """
        import random

        retry_count = 0
        while True:
            if stop_event and stop_event.is_set():
                logger.info("listen_messages detenido por stop_event")
                break
            try:
                with self._xmpp_session(token) as sock:
                    self._listen_loop(sock, callback, stop_event=stop_event)
                retry_count = 0  # Reset en conexión exitosa
            except TokenExpiredError:
                raise
            except (ConnectionLostError, OSError, socket.error) as e:
                retry_count += 1
                if max_retries > 0 and retry_count >= max_retries:
                    raise ConnectionLostError(f"Max reintentos ({max_retries}) alcanzados") from e
                backoff = min(base_backoff * (2 ** (retry_count - 1)), max_backoff)
                # Añadir jitter ±20%
                backoff *= random.uniform(0.8, 1.2)
                logger.warning("Reconectando en %.1fs (intento %d)%s", backoff, retry_count,
                               f" / {max_retries}" if max_retries else "")
                if stop_event:
                    stop_event.wait(backoff)
                else:
                    time.sleep(backoff)

    def _listen_loop(self, sock, callback: Callable[[dict], None], stop_event: threading.Event = None) -> None:
        """Loop interno de recepción de stanzas.

        Fix v1.9.1: ``stop_event`` es el event que pasa el caller y SOLO el
        caller debe setearlo. El keepalive worker usa un event interno
        ``ka_stop`` para no contaminar el del caller. Antes, el ``finally``
        hacía ``stop_event.set()`` para parar el keepalive — pero como
        recibía el mismo event del caller, lo dejaba seteado para siempre
        y el caller creía que el usuario había pedido parar cuando en
        realidad fue un fallo de red. Eso provocaba que bots que pasaban
        su propio ``stop_event`` se apagaran al primer envío de respuesta.
        """
        # Event interno solo para el keepalive worker; no se comparte con
        # el caller, así el finally puede setearlo sin contaminer a nadie.
        ka_stop = threading.Event()
        ping_id = util.generate_token(5)
        ka = threading.Thread(
            target=self._keepalive_worker,
            args=(sock, ka_stop, ping_id),
            daemon=True,
        )
        ka.start()
        self._xml_parser.reset()

        try:
            while not (stop_event and stop_event.is_set()):
                try:
                    response = self._recv_all(sock)
                except OSError as e:
                    raise ConnectionLostError(e)

                if response is None:
                    raise ConnectionLostError("Servidor cerro conexion")

                if response == "":
                    continue

                stanzas = self._xml_parser.feed(response)

                for msg in stanzas:
                    # usar helper para manejar cada stanza parseada
                    try:
                        # Enriquecer mensajes de grupo si hay GroupClient disponible
                        if msg.get("type") == "gc" and hasattr(self, "_group_client") and self._group_client:
                            msg = self._group_client.process_group_message(msg)
                        self.handle_parsed_stanza(msg, sock=sock, callback=callback)
                    except Exception:
                        logger.exception("Error manejando stanza parseada")

        finally:
            # Solo detener el keepalive interno; NO tocar stop_event del caller.
            ka_stop.set()
            self._xml_parser.reset()

    def _keepalive_worker(self, sock, stop: threading.Event, ping_id: str) -> None:
        while not stop.is_set():
            stop.wait(constants.KEEPALIVE_INTERVAL)
            if stop.is_set():
                break
            try:
                sock.sendall(stanza.ping(ping_id).encode())
            except OSError:
                break

    def handle_parsed_stanza(
        self,
        msg: dict,
        *,
        sock=None,
        callback: Callable[[dict], None] | None = None,
    ) -> list[str]:
        """Maneja una stanza ya parseada.

        - Envía receipts si corresponde (requiere `sock`).
        - Despacha eventos al `EventBus` para tipos: message, presence, iq, ack,
          receipt, deleted, chat_state.
        - Llama al `callback` si está provisto.

        Retorna la lista de tipos de evento despachados.
        """
        dispatched = []

        # Deduplicación LRU: saltar mensajes ya procesados.
        msg_id = msg.get("id", "")
        if msg_id and hasattr(self, "_seen_msg_ids"):
            if msg_id in self._seen_msg_ids:
                # Mover al final para mantener LRU (últimamente accedido)
                self._seen_msg_ids.move_to_end(msg_id)
                return dispatched
            self._seen_msg_ids[msg_id] = None
            # Podar de forma determinista (más viejos primero)
            max_size = getattr(self, "_seen_msg_ids_max", 10000)
            trim_to = getattr(self, "_seen_msg_ids_trim_to", 5000)
            if len(self._seen_msg_ids) > max_size:
                # Eliminar los más viejos hasta llegar a trim_to
                while len(self._seen_msg_ids) > trim_to:
                    self._seen_msg_ids.popitem(last=False)

        # determinar si es 'mensaje' (contenido multimedia/texto)
        is_content = (
            msg.get("body")
            or msg.get("url")
            or msg.get("contact_id")
            or msg.get("sticker_id")
            or msg.get("video_url")
            or msg.get("voice_url")
            or msg.get("gif_url")
            or msg.get("stream_url")
            or msg.get("buttons")
            or msg.get("location_id")
            or msg.get("reaction_code")
        )

        # enviar receipt de entrega (received/rd) para mensajes con contenido
        # si no es borrado (comportamiento del cliente oficial)
        if is_content and not msg.get("deleted"):
            msg_id = msg.get("id", "")
            msg_from = msg.get("from", "")
            if msg_id and msg_from and sock is not None:
                try:
                    receipt = stanza.receipt(msg_from, msg_id)
                    sock.sendall(receipt.encode())
                except Exception:
                    logger.exception("Error enviando receipt")

        # Despachar tipos básicos
        try:
            if hasattr(self, "events") and self.events is not None:
                # message
                if is_content or msg.get("chat_state") or msg.get("deleted"):
                    try:
                        self.events.dispatch("message", msg)
                        dispatched.append("message")
                    except Exception:
                        logger.exception("Error despachando 'message'")

                # presence
                if "status" in msg or "show" in msg or "priority" in msg:
                    try:
                        self.events.dispatch("presence", msg)
                        dispatched.append("presence")
                    except Exception:
                        logger.exception("Error despachando 'presence'")

                # iq
                if "query" in msg or "error" in msg or msg.get("type") == "iq":
                    try:
                        self.events.dispatch("iq", msg)
                        dispatched.append("iq")
                    except Exception:
                        logger.exception("Error despachando 'iq'")

                # ack (oficial) y tdack (legado)
                if msg.get("type") in ("ack", "tdack") or msg.get("ack"):
                    try:
                        self.events.dispatch("ack", msg)
                        dispatched.append("ack")
                    except Exception:
                        logger.exception("Error despachando 'ack'")

                # receipt (deliver/read)
                if msg.get("receipt"):
                    try:
                        self.events.dispatch("receipt", msg)
                        dispatched.append("receipt")
                    except Exception:
                        logger.exception("Error despachando 'receipt'")

                # deleted
                if msg.get("deleted"):
                    try:
                        self.events.dispatch("deleted", msg)
                        dispatched.append("deleted")
                    except Exception:
                        logger.exception("Error despachando 'deleted'")

                # chat_state
                if msg.get("chat_state"):
                    try:
                        self.events.dispatch("chat_state", msg)
                        dispatched.append("chat_state")
                    except Exception:
                        logger.exception("Error despachando 'chat_state'")
        except Exception:
            logger.exception("Error durante dispatch de eventos")

        # finalmente, llamar al callback tradicional
        if callback:
            try:
                callback(msg)
            except Exception:
                logger.exception("Error en callback del usuario")

        return dispatched
