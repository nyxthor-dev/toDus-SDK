import logging
import threading
import time
import socket
import hashlib
from typing import Callable
from .. import util, stanza, constants
from ..errors import TokenExpiredError, ConnectionLostError
from ..types import FileType

logger = logging.getLogger("todus")


class ToDusMessageMixin:
    """Mixin que contiene la lógica de mensajería (envío y recepción) de ToDus."""

    # --- Mensajeria Privada ---

    def send_message(self, token: str, to_jid: str, body: str, reply_to_id: str = "") -> str:
        """Envía mensaje de texto privado. Retorna el msg_id generado."""
        mid = util.generate_token(8)
        msg = stanza.message(to_jid, body, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def edit_message(self, token: str, to_jid: str, new_body: str, original_msg_id: str, reply_to_id: str = "") -> str:
        """Edita un mensaje privado."""
        edit_id = util.generate_token(8)
        msg = stanza.edit_message(to_jid, new_body, original_msg_id, edit_id=edit_id, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return edit_id

    def send_file_message(self, token: str, to_jid: str, url: str, file_type: FileType,
                          caption: str = "", file_name: str = "", file_size: int = 0,
                          reply_to_id: str = "") -> str:
        mid = util.generate_token(8)
        msg = stanza.file_message(to_jid, url, int(file_type), caption, msg_id=mid,
                                  file_name=file_name, file_size=file_size, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_image_message(self, token: str, to_jid: str, url: str, file_name: str,
                           file_size: int, width: int = 0, height: int = 0,
                           thumbnail: str = "", caption: str = "", reply_to_id: str = "") -> str:
        """Envía mensaje privado con imagen adjunta."""
        mid = util.generate_token(8)
        msg = stanza.image_message(to_jid, url, file_name, file_size, width, height,
                                   thumbnail, caption, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_image_message_simple(self, token: str, to_jid: str, url: str,
                                  file_name: str, file_size: int, msg_id: str = "",
                                  reply_to_id: str = "") -> str:
        """Envía mensaje privado con imagen SIN metadata."""
        mid = msg_id or util.generate_token(8)
        msg = stanza.image_message_simple(to_jid, url, file_name, file_size,
                                          msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_button_message(self, token: str, to_jid: str, text: str, buttons: list[dict],
                            reply_to_id: str = "") -> str:
        """Envía mensaje con botones interactivos."""
        mid = util.generate_token(8)
        msg = stanza.button_message(to_jid, text, buttons, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_contact_message(self, token: str, to_jid: str, contact_id: str,
                             contact_name: str, contact_phone: str, reply_to_id: str = "") -> str:
        mid = util.generate_token(8)
        msg = stanza.contact_message(to_jid, contact_id, contact_name, contact_phone,
                                     msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_sticker_message(self, token: str, to_jid: str, sticker_id: str,
                             sticker_name: str, sticker_pack: str, sticker_hash: str,
                             reply_to_id: str = "") -> str:
        mid = util.generate_token(8)
        msg = stanza.sticker_message(to_jid, sticker_id, sticker_name, sticker_pack,
                                     sticker_hash, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_video_message(self, token: str, to_jid: str, url: str, video_id: str,
                           file_name: str, file_size: int, duration: int,
                           width: int, height: int, thumbnail: str,
                           info_text: str = "", reply_to_id: str = "") -> str:
        mid = hashlib.md5(util.generate_token(16).encode()).hexdigest()
        msg = stanza.video_message(to_jid, url, video_id, file_name, file_size,
                                   duration, width, height, thumbnail,
                                   msg_id=mid, info_text=info_text, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_location_message(self, token: str, to_jid: str, lat: float, lon: float,
                              zoom: float = 11.0, text: str = "", reply_to_id: str = "") -> str:
        """Envía un mensaje con ubicación adjunta."""
        mid = util.generate_token(8)
        msg = stanza.location_message(to_jid, lat, lon, zoom, text, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_event_message(self, token: str, to_jid: str, title: str, start: int,
                           end: int, all_day: bool, ics_data: str,
                           event_id: str = "", reply_to_id: str = "") -> str:
        """Envía un mensaje con evento/calendario adjunto."""
        mid = util.generate_token(8)
        msg = stanza.event_message(to_jid, event_id, title, start, end, all_day,
                                   ics_data, msg_id=mid, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return mid

    def send_chat_state(self, token: str, to_jid: str, state: str) -> None:
        st = stanza.chat_state(to_jid, state)
        with self._xmpp_session(token) as sock:
            sock.send(st.encode())

    def delete_message(self, token: str, to_jid: str, message_id: str,
                       msg_type: str = "c", body: str = "", media_xml: str = "",
                       reply_to_id: str = "") -> str:
        """Elimina un mensaje propio."""
        msg = stanza.delete_message(to_jid, message_id, msg_id=message_id, msg_type=msg_type,
                                    body=body, media_xml=media_xml, reply_to_id=reply_to_id)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return message_id

    def send_read_receipt(self, token: str, to_jid: str, msg_id: str, msg_type: str = "c") -> str:
        """Envía una confirmación de lectura (read receipt)."""
        rid = util.generate_token(8)
        msg = stanza.read_receipt(to_jid, msg_id, receipt_id=rid, msg_type=msg_type)
        with self._xmpp_session(token) as sock:
            sock.send(msg.encode())
        return rid

    # --- Recepción de mensajes ---

    def listen_messages(self, token: str, callback: Callable[[dict], None]) -> None:
        while True:
            try:
                with self._xmpp_session(token) as sock:
                    self._listen_loop(sock, callback)
            except TokenExpiredError:
                raise
            except (ConnectionLostError, OSError, socket.error):
                time.sleep(15)

    def _listen_loop(self, sock, callback: Callable[[dict], None]) -> None:
        stop_event = threading.Event()
        ping_id = util.generate_token(5)
        ka = threading.Thread(
            target=self._keepalive_worker,
            args=(sock, stop_event, ping_id),
            daemon=True,
        )
        ka.start()
        self._xml_parser.reset()

        try:
            while True:
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
                    is_content = (
                        msg.get("body")
                        or msg.get("url")
                        or msg.get("contact_id")
                        or msg.get("sticker_id")
                        or msg.get("video_url")
                        or msg.get("buttons")
                        or msg.get("location_id")
                    )
                    
                    if is_content and not msg.get("deleted"):
                        msg_id = msg.get("id", "")
                        msg_from = msg.get("from", "")
                        if msg_id and msg_from:
                            try:
                                receipt = stanza.receipt(msg_from, msg_id)
                                sock.send(receipt.encode())
                            except Exception:
                                pass
                    
                    if (
                        is_content
                        or msg.get("chat_state")
                        or msg.get("receipt")
                        or msg.get("deleted")
                    ):
                        # Primero despachar al event bus si existe
                        try:
                            if hasattr(self, "events") and self.events is not None:
                                try:
                                    self.events.dispatch("message", msg)
                                except Exception:
                                    logger.exception("Error despachando evento 'message'")
                        except Exception:
                            # protección adicional por si `events` causa fallos
                            logger.exception("Error comprobando `events` en cliente")

                        # Llamada al callback tradicional
                        callback(msg)

        finally:
            stop_event.set()
            self._xml_parser.reset()

    def _keepalive_worker(self, sock, stop: threading.Event, ping_id: str) -> None:
        while not stop.is_set():
            time.sleep(constants.KEEPALIVE_INTERVAL)
            if stop.is_set():
                break
            try:
                sock.send(stanza.ping(ping_id).encode())
            except OSError:
                break
