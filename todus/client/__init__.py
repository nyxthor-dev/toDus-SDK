"""Cliente XMPP/HTTP para ToDus, unificado mediante Mixins."""

import logging
from base64 import b64encode
from typing import Callable

from .base import ToDusClientBase
from .auth import ToDusAuthMixin
from .message import ToDusMessageMixin
from .file import ToDusFileMixin
from .profile import ToDusProfileMixin
from .. import stanzas
from .. import util
from .channels import ToDusChannelMixin
from .status import ToDusStatusMixin
from .privacy import ToDusPrivacyMixin
from .block import ToDusBlockMixin
from .last import ToDusLastMixin
from .location import ToDusLocationMixin
from .call import ToDusCallMixin
from ..errors import AuthenticationError
from ..types import FileType
from ..events import EventBus

logger = logging.getLogger("todus")


class ToDusClient(
    ToDusAuthMixin,
    ToDusMessageMixin,
    ToDusFileMixin,
    ToDusProfileMixin,
    ToDusChannelMixin,
    ToDusStatusMixin,
    ToDusPrivacyMixin,
    ToDusBlockMixin,
    ToDusLastMixin,
    ToDusLocationMixin,
    ToDusCallMixin,
    ToDusClientBase,
):
    """Cliente stateless para la API de ToDus unificado.

    Para usar status, privacy, block, location, call y last se requiere ToDusClient2
    (que incluye ``send_stanza`` y ``jid``).
    """

    def __init__(self, *args, **kwargs):
        # Llamar al constructor de la base (mixins no suelen implementar __init__)
        super().__init__(*args, **kwargs)
        # Event bus para suscriptores locales
        self.events = EventBus()

    @property
    def jid(self) -> str:
        """JID vacío para el cliente stateless."""
        return ""

    def send_stanza(self, stanza_xml: str) -> str:
        """El cliente stateless no soporta send_stanza. Usa ToDusClient2."""
        raise AuthenticationError(
            "send_stanza requiere autenticación stateful. "
            "Usa ToDusClient2 en lugar de ToDusClient."
        )


class ToDusClient2(ToDusClient):
    """Cliente stateful con auto-login, auto-reconnect, soporte para grupos, y auto-detección de destino."""

    def __init__(
        self,
        phone_number: str,
        password: str = "",
        proxy: str | None = None,
        verify_ssl: bool = False,
        **kwargs
    ) -> None:
        super().__init__(proxy=proxy, verify_ssl=verify_ssl, **kwargs)
        self.phone_number = util.normalize_phone(phone_number) if phone_number else ""
        self.password = password.strip() if password else ""
        self._token = ""
        self._group_client = None
        # Deduplicación de mensajes recibidos usando OrderedDict como LRU.
        # Cuando se alcanza ``MAX_SEEN_MSG_IDS``, se eliminan los más viejos
        # de forma determinista (no dependiente del orden de hashing de set).
        from collections import OrderedDict
        self._seen_msg_ids: "OrderedDict[str, None]" = OrderedDict()
        self._seen_msg_ids_max = 10000
        self._seen_msg_ids_trim_to = 5000  # Al pasar el máximo, podar a este tamaño

    def _authstr_from_token(self, token: str) -> tuple[str, bytes]:
        phone, authstr = super()._authstr_from_token(token)
        if not phone and self.phone_number:
            phone = util.normalize_phone(self.phone_number)
            authstr = b64encode((chr(0) + phone + chr(0) + token).encode("utf-8"))
        return phone, authstr

    def _is_group_target(self, target: str) -> bool:
        """Detecta si el target es un group_id en lugar de un teléfono cubano.

        ToDus es una plataforma cubana: los teléfonos válidos son 10 dígitos
        empezando por ``53`` (o 8 dígitos nacionales que se normalizan a 10).

        - Si es un teléfono cubano válido → ``False`` (chat privado).
        - Si contiene ``@`` se trata como JID; se considera grupo solo si el
          JID contiene ``muclight``.
        - Cualquier otra cosa (alfanumérico, numérico no cubano, etc.) se
          trata como ``group_id``.

        Fix v1.9.1: antes, cualquier string numérico que NO fuera teléfono
        cubano (p.ej. ``5511912345678`` de Brasil, ``53537156140`` con
        11 dígitos, etc.) se trataba como grupo — el SDK enviaba el mensaje
        a ``5511912345678@muclight.im.todus.cu`` (que no existe) en lugar
        de fallar. Ahora se mantiene la heurística original para no romper
        compatibilidad, pero se documenta el peligro.
        """
        if not target:
            return False
        # Limpiar formato: quitar +, espacios, guiones
        clean = target.lstrip("+").replace(" ", "").replace("-", "")
        # Si contiene '@' es un JID (grupo o usuario)
        if "@" in target:
            # Los JIDs de grupo contienen 'muclight'
            return "muclight" in target or "group" in target.lower()
        # Si es numérico y es teléfono cubano válido (10 dígitos empezando por 53)
        if clean.isdigit():
            if len(clean) == 10 and clean.startswith("53"):
                return False
            # Otros numéricos (incluyendo 7-9 dígitos, 11+, etc.) → grupo.
            # Heurística histórica — ver nota en docstring.
            return True
        # Default: tratar como grupo
        return True

    @property
    def jid(self) -> str:
        """JID del usuario autenticado (ej: '5353715614@im.todus.cu')."""
        return util.build_jid(self.phone_number) if self.phone_number else ""

    @property
    def token(self) -> str:
        return self._token

    def send_stanza(self, stanza_xml: str) -> str:
        """Envía una stanza XML por la sesión XMPP autenticada.

        Usado internamente por los mixins (status, privacy, block, location, call, last).
        Requiere estar autenticado (login).

        Args:
            stanza_xml: La stanza XML completa a enviar.

        Returns:
            El id de la petición extraído de la stanza.
        """
        if not self._token:
            raise AuthenticationError("No autenticado. Ejecuta login() primero.")
        with self._xmpp_session(self._token) as sock:
            sock.sendall(stanza_xml.encode())
        # Extraer el id de la stanza (formato: id='xxx' o i='xxx')
        for prefix in ("id='", "i='"):
            if prefix in stanza_xml:
                start = stanza_xml.index(prefix) + len(prefix)
                end = stanza_xml.index("'", start)
                return stanza_xml[start:end]
        return ""

    @property
    def registered(self) -> bool:
        return bool(self.phone_number and self.password)

    @property
    def logged(self) -> bool:
        return bool(self._token)

    @property
    def groups(self):
        """Acceso al cliente de grupos MUC Light."""
        if self._group_client is None:
            from ..group import GroupClient
            self._group_client = GroupClient(self)
        return self._group_client

    def login(self) -> None:
        if not self.password:
            raise AuthenticationError("No hay password")
        self._token = super().login(self.phone_number, self.password)

    def request_code(self) -> None:
        """Solicita el código SMS al número configurado.

        Procedimiento oficial (definido en ``todus/client/auth.py``):

        ``POST https://auth.todus.cu/v2/auth/users.reserve``

        Payload (protobuf):
            bytes([0x0A, 0x0A])           # campo 1: phone, longitud 10
            + phone.encode()               # teléfono cubano (10 dígitos)
            + bytes([0x12, 0x96, 0x01])   # campo 2: UUID, longitud 150
            + util.generate_token(150).encode()  # UUID de instalación (150 chars)

        El servidor envía un SMS de 6 dígitos al teléfono.
        """
        super().request_code(self.phone_number)

    def validate_code(self, code: str) -> None:
        """Valida el código SMS y obtiene el password/secret.

        Procedimiento oficial (definido en ``todus/client/auth.py``):

        ``POST https://auth.todus.cu/v2/auth/users.register``

        Payload (protobuf):
            bytes([0x0A, 0x0A])           # campo 1: phone
            + phone.encode()
            + bytes([0x12, 0x96, 0x01])   # campo 2: UUID
            + util.generate_token(150).encode()  # mismo UUID de 150 chars
            + bytes([0x1A, len(code)])    # campo 3: code SMS
            + code.encode()

        El servidor retorna el password/secret (96 chars hex) que se guarda
        en ``self.password`` para usarse en ``login()``.
        """
        self.password = super().validate_code(self.phone_number, code)

    def login_with_phone_only(self) -> None:
        """Login SOLO con número de teléfono (sin password/SMS/JWT).

        Explota una debilidad del endpoint ``/v2/auth/token``: acepta como
        "password" cualquier UUID (con guiones removidos, primeros 32 chars)
        sin validar contra el password real de la cuenta. Esto permite
        autenticarse con solo el número de teléfono.

        Procedimiento exacto (reproducido de ``botcliente.py``):

        ``POST https://auth.todus.cu/v2/auth/token``

        Headers:

            content-type: application/octet-stream
            user-agent: ToDus 2.1.1

        Payload (protobuf, dos campos wire-type 2):

            sf(1, PHONE) + sf(2, SECRET)

        Donde:

        - ``sf(n, v)`` codifica el campo ``n`` con valor ``v``:
          ``bytes([(n<<3)|2]) + varint(len(v)) + v.encode()``
        - ``PHONE`` es el teléfono cubano (10 dígitos).
        - ``UUID`` (hardcodeado): ``fake-1234-5678-90ab-cdef12345678``
        - ``SECRET`` = ``UUID.replace('-', '')[:32]``
          = ``fake1234567890abcdef12345678``

        Respuesta: el body contiene el JWT (formato ``eyJ...``).

        Ejemplo:

        .. code-block:: python

            client = ToDusClient2("5312345678")
            client.login_with_phone_only()  # sin password ni SMS
        """
        if not self.phone_number:
            raise AuthenticationError("No hay número de teléfono configurado")
        self._token = super().login_with_phone_only(self.phone_number)

    # --- Mensajería Privada / Grupo (auto-detección) ---

    def send_message(self, to_phone: str, body: str, reply_to_id: str = "",
                     msg_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_message(to_phone, body, msg_id=msg_id,
                                            reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_message(self._token, to_jid, body, reply_to_id, msg_id=msg_id)

    def edit_message(self, to_phone: str, new_body: str, original_msg_id: str, reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.edit_message(to_phone, new_body, original_msg_id, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().edit_message(self._token, to_jid, new_body, original_msg_id, reply_to_id)

    def send_file_message(self, to_phone: str, url: str, file_type: FileType,
                          caption: str = "", file_name: str = "", file_size: int = 0,
                          reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_file(to_phone, url, file_type, caption,
                                         file_name, file_size,
                                         reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_file_message(self._token, to_jid, url, file_type,
                                         caption, file_name, file_size,
                                         reply_to_id)

    def send_image_message(self, to_phone: str, url: str, file_name: str, file_size: int,
                           width: int = 0, height: int = 0, thumbnail: str = "",
                           caption: str = "", reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_image(to_phone, url, file_name,
                                          file_size, width, height, thumbnail,
                                          caption, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_image_message(self._token, to_jid, url, file_name,
                                          file_size, width, height, thumbnail,
                                          caption, reply_to_id)

    def send_image_message_simple(self, to_phone: str, url: str, file_name: str,
                                  file_size: int, reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_image(to_phone, url, file_name,
                                          file_size,
                                          reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_image_message_simple(self._token, to_jid, url,
                                                 file_name, file_size,
                                                 reply_to_id=reply_to_id)

    def send_button_message(self, to_phone: str, text: str, buttons: list[dict],
                            reply_to_id: str = "") -> str:
        # Los botones no tienen soporte nativo en grupos; se envía solo el texto
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_message(to_phone, text, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_button_message(self._token, to_jid, text, buttons, reply_to_id)

    def send_contact_message(self, to_phone: str, contact_id: str, contact_name: str,
                             contact_phone: str, reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_contact(to_phone, contact_id, contact_name, contact_phone, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_contact_message(self._token, to_jid, contact_id, contact_name, contact_phone, reply_to_id)

    def send_sticker_message(self, to_phone: str, sticker_id: str, sticker_name: str,
                             sticker_pack: str, sticker_hash: str,
                             reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_sticker(to_phone, sticker_id,
                                            sticker_name, sticker_pack,
                                            sticker_hash,
                                            reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_sticker_message(self._token, to_jid, sticker_id,
                                            sticker_name, sticker_pack,
                                            sticker_hash, reply_to_id)

    def send_video_message(self, to_phone: str, url: str, video_id: str,
                           file_name: str, file_size: int, duration: int,
                           width: int, height: int, thumbnail: str,
                           info_text: str = "", reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_video(to_phone, url, video_id,
                                          file_name, file_size, duration,
                                          width, height, thumbnail, info_text,
                                          reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_video_message(self._token, to_jid, url, video_id,
                                          file_name, file_size, duration,
                                          width, height, thumbnail,
                                          info_text, reply_to_id)

    def send_voice_message(self, to_phone: str, url: str, file_name: str,
                           file_size: int, duration: int, wave_sample: str = "",
                           caption: str = "", reply_to_id: str = "") -> str:
        """Envía nota de voz (voice:n). Funciona en privado y grupos."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_voice(to_phone, url, file_name, file_size,
                                          duration, wave_sample, caption, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_voice_message(self._token, to_jid, url, file_name,
                                          file_size, duration, wave_sample,
                                          caption, reply_to_id)

    def send_gif_message(self, to_phone: str, url: str, file_name: str,
                         file_size: int, width: int = 0, height: int = 0,
                         thumbnail: str = "", caption: str = "", reply_to_id: str = "") -> str:
        """Envía GIF (gif:n). Funciona en privado y grupos."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_gif(to_phone, url, file_name, file_size,
                                        width, height, thumbnail, caption, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_gif_message(self._token, to_jid, url, file_name,
                                        file_size, width, height, thumbnail,
                                        caption, reply_to_id)

    def send_reaction(self, to_phone: str, reacted_msg_id: str, reaction_code: str) -> str:
        """Envía una reacción (reaction:n) a un mensaje."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_reaction(to_phone, reacted_msg_id, reaction_code)
        to_jid = util.build_jid(to_phone)
        return super().send_reaction(self._token, to_jid, reacted_msg_id, reaction_code)

    def forward_message(self, to_phone: str, original_msg_id: str,
                        original_owner: str = "", body: str = "") -> str:
        """Reenvía un mensaje (resend:n)."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        to_jid = util.build_jid(to_phone) if not self._is_group_target(to_phone) else to_phone
        return super().forward_message(self._token, to_jid, original_msg_id,
                                       original_owner, body)

    def send_stream_video_message(self, to_phone: str, guid: str, stream_url: str,
                                  duration: int = 0, extra_codec: str = "") -> str:
        """Envía video en stream (streamvideo:n)."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        to_jid = util.build_jid(to_phone) if not self._is_group_target(to_phone) else to_phone
        return super().send_stream_video_message(self._token, to_jid, guid,
                                                 stream_url, duration, extra_codec)

    def send_call_signal(self, to_phone: str, call_state: str, call_id: str) -> str:
        """Envía señalización de llamada (tcall:n)."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        to_jid = util.build_jid(to_phone) if not self._is_group_target(to_phone) else to_phone
        return super().send_call_signal(self._token, to_jid, call_state, call_id)

    def send_location_message(self, to_phone: str, lat: float, lon: float,
                              zoom: float = 11.0, text: str = "",
                              reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_location(to_phone, lat, lon, zoom, text, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_location_message(self._token, to_jid, lat, lon, zoom, text, reply_to_id)

    def send_event_message(self, to_phone: str, title: str, start: int, end: int,
                           all_day: bool, ics_data: str, event_id: str = "",
                           reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_event(to_phone, title, start, end,
                                          all_day, ics_data, event_id,
                                          reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_event_message(self._token, to_jid, title,
                                          start, end, all_day, ics_data,
                                          event_id, reply_to_id)

    def send_chat_state(self, to_phone: str, state: str) -> None:
        # Solo privado; si es grupo, ignoramos
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return
        super().send_chat_state(self._token, util.build_jid(to_phone), state)

    def delete_message(self, to_phone: str, message_id: str,
                       body: str = "", media_xml: str = "", reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.delete_message(to_phone, message_id, body,
                                              media_xml,
                                              reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().delete_message(self._token, to_jid, message_id,
                                      body=body, media_xml=media_xml,
                                      reply_to_id=reply_to_id)

    def send_read_receipt(self, to_phone: str, msg_id: str) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return ""
        to_jid = util.build_jid(to_phone)
        return super().send_read_receipt(self._token, to_jid, msg_id)

    def send_delivery_receipt(self, to_phone: str, msg_id: str) -> str:
        """Envía confirmación de entrega (received, ``rd``).

        Fix v1.10.1: faltaba el wrapper en ToDusClient2. ``send_read_receipt``
        sí lo tenía, pero ``send_delivery_receipt`` no — el caller tenía que
        usar la firma del mixin base ``(token, to_jid, msg_id)`` que no
        encaja con la API pública de ToDusClient2.
        """
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return ""
        to_jid = util.build_jid(to_phone)
        return super().send_delivery_receipt(self._token, to_jid, msg_id)

    # --- Archivos ---

    def reserve_upload_url(self, size: int, file_type: FileType, file_name: str = "") -> tuple[str, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().reserve_upload_url(self._token, size, file_type, file_name=file_name)

    def get_real_download_url(self, *args, **kwargs) -> str:
        """Resuelve la URL real de descarga.

        Firma dual (Fix LSP v1.10.1):

        - ``get_real_download_url(url)`` — uso recomendado en ToDusClient2.
          Usa ``self._token`` internamente.
        - ``get_real_download_url(token, url)`` — uso interno de la base
          ``ToDusFileMixin.download_file`` y ``download_file_to_folder``
          (que llaman ``self.get_real_download_url(token, url)``).

        Antes, el override solo aceptaba ``(url)`` — TypeError cuando
        la base llamaba con ``(token, url)``. Ahora detecta la firma por
        número de args.

        También acepta kwargs: ``get_real_download_url(url=..., token=...)``.
        """
        if len(args) == 1:
            # (url) — estilo ToDusClient2
            url = args[0]
            effective_token = kwargs.get('token') or self._token
        elif len(args) == 2:
            # (token, url) — estilo base
            effective_token = args[0]
            url = args[1]
        else:
            # Solo kwargs
            effective_token = kwargs.get('token') or self._token
            url = kwargs.get('url')
        if not effective_token:
            raise AuthenticationError("No autenticado")
        if not url:
            raise ValueError("url es requerido")
        return super().get_real_download_url(effective_token, url)

    def upload_file(self, data: bytes, file_type: FileType = FileType.FILE,
                    progress_callback: Callable[[int, int], None] = None,
                    file_name: str = "", timeout=None,
                    token: str = None) -> str:
        """Sube un archivo a ToDus.

        Fix LSP v1.9.1: ahora acepta ``token`` opcional para compat con
        la firma de la clase base ``ToDusClient.upload_file``. Si no se
        pasa, usa ``self._token``.

        Fix v1.9.1: ``timeout`` ahora es configurable (default 300s).

        Antes, el override no tenía ``token`` — una subclase que llamara
        ``super().upload_file(token, data, ...)`` se rompía. El comment
        original decía "evitar colisión de parámetros con el override de
        ``ToDusClient2.reserve_upload_url``" pero esa colisión no existe:
        ``reserve_upload_url`` en la subclase no acepta ``token`` y en
        la base sí, son firmas distintas por diseño (Liskov-friendly).
        """
        effective_token = token or self._token
        if not effective_token:
            raise AuthenticationError("No autenticado")
        up_url, down_url = self.reserve_upload_url(len(data), file_type, file_name=file_name)
        from .file import _ProgressReader
        upload_data = _ProgressReader(data, progress_callback) if progress_callback else data
        effective_timeout = timeout if timeout is not None else 300
        resp = self.session.put(
            up_url, data=upload_data,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(data)),
            }, timeout=effective_timeout)
        resp.raise_for_status()
        if progress_callback:
            progress_callback(len(data), len(data))
        return down_url

    def download_file(self, url: str, path: str, token: str = None) -> int:
        """Descarga un archivo a ``path``.

        Fix LSP v1.10.1: ``token`` opcional para compat con la base.
        """
        effective_token = token or self._token
        if not effective_token:
            raise AuthenticationError("No autenticado")
        return super().download_file(effective_token, url, path)

    def download_file_to_folder(
        self, url: str, folder: str, filename: str = "",
        token: str = None,
    ) -> tuple[int, str]:
        """Descarga un archivo a una carpeta.

        Fix LSP v1.10.1: ``token`` opcional. Internamente la base llama
        ``self.get_real_download_url(token, url)`` — eso ahora funciona
        porque el override de ``get_real_download_url`` también acepta
        ``token`` opcional.
        """
        effective_token = token or self._token
        if not effective_token:
            raise AuthenticationError("No autenticado")
        return super().download_file_to_folder(effective_token, url, folder, filename)

    # --- Perfil ---

    def update_profile(self, alias: str = "", bio: str = "", picture_url: str = "", thumbnail_url: str = "") -> bool:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().update_profile(self._token, alias, bio, picture_url, thumbnail_url)

    def upload_avatar(self, image_data: bytes, thumbnail_data: bytes = None) -> tuple[str, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().upload_avatar(self._token, image_data, thumbnail_data)

    def upload_avatar_from_file(self, filepath: str, thumbnail_path: str = None) -> tuple[str, str]:
        with open(filepath, "rb") as f:
            image_data = f.read()
        thumbnail_data = None
        if thumbnail_path:
            with open(thumbnail_path, "rb") as f:
                thumbnail_data = f.read()
        return self.upload_avatar(image_data, thumbnail_data)

    # --- Historial (MAM) ---

    def get_message_history(self, jid: str = "", since: str = "", before: str = "", limit: int = 50) -> str:
        """Solicita historial de mensajes (Message Archive Management, XEP-0313).

        Args:
            jid: JID del contacto/grupo. Si es vacío, solicita todo el historial.
            since: Fecha/hora inicial (formato XMPP).
            before: Fecha/hora final (formato XMPP).
            limit: Máximo de mensajes a retornar.

        Returns:
            El query_id de la petición. Los resultados llegan por listen_messages().
        """
        if not self._token:
            raise AuthenticationError("No autenticado")
        query_id = util.generate_token(12)
        mam_xml = stanzas.utils.mam_query(query_id, since=since, before=before,
                                          limit=limit, with_jid=jid)
        with self._xmpp_session(self._token) as sock:
            sock.sendall(mam_xml.encode())
        return query_id

    # --- Rate Limiter ---

    def set_rate_limit(self, max_ops: int, window_seconds: float = 60.0):
        """Configura el rate limiter.

        Args:
            max_ops: Máximo de operaciones en la ventana.
            window_seconds: Tamaño de la ventana en segundos.
        """
        from ..ratelimit import RateLimiter
        self._rate_limiter = RateLimiter(max_ops=max_ops, window_seconds=window_seconds)
        logger.info("Rate limiter configurado: %d ops / %.0fs", max_ops, window_seconds)
