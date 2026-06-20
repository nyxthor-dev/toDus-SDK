"""Cliente XMPP/HTTP para ToDus, unificado mediante Mixins."""

import logging
import socket
import time
from base64 import b64encode
from typing import Callable

from .base import ToDusClientBase
from .auth import ToDusAuthMixin
from .message import ToDusMessageMixin
from .file import ToDusFileMixin
from .profile import ToDusProfileMixin
from ..errors import AuthenticationError, TokenExpiredError, ConnectionLostError
from ..types import FileType
from .. import util, stanza

logger = logging.getLogger(__name__)


class ToDusClient(
    ToDusAuthMixin,
    ToDusMessageMixin,
    ToDusFileMixin,
    ToDusProfileMixin,
    ToDusClientBase,
):
    """Cliente stateless para la API de ToDus unificado."""
    pass


class ToDusClient2(ToDusClient):
    """
    Cliente stateful con auto-login, auto-reconnect, soporte para grupos
    y resolución automática de JIDs.
    """

    def __init__(self, phone_number: str, password: str = "", proxy: str | None = None, **kwargs) -> None:
        super().__init__(proxy=proxy, **kwargs)
        self.phone_number = phone_number
        self.password = password
        self._token = ""
        self._group_client = None

    def _authstr_from_token(self, token: str) -> tuple[str, bytes]:
        phone, authstr = super()._authstr_from_token(token)
        if not phone and self.phone_number:
            phone = util.normalize_phone(self.phone_number)
            authstr = b64encode((chr(0) + phone + chr(0) + token).encode("utf-8"))
        return phone, authstr

    # ================================================================
    #  RESOLUCIÓN AUTOMÁTICA DE JIDs
    # ================================================================

    def _is_group_target(self, target: str) -> bool:
        """Detecta si el target es un grupo (cualquier formato)."""
        resolved = util.resolve_target(target)
        return resolved['type'] == 'group'

    def resolve_target(self, target: str) -> dict:
        """
        Resuelve automáticamente cualquier formato de destino.
        Útil para saber qué tipo de destino es antes de enviar.
        """
        return util.resolve_target(target)

    def get_contact_name(self, phone: str) -> Optional[str]:
        """
        Obtiene el nombre de un contacto.
        Primero busca en caché, si no, hace una consulta vCard (pendiente de implementar).
        """
        # Buscar en caché
        cached = util.get_cached_contact(phone)
        if cached:
            return cached
        
        # TODO: Implementar consulta vCard para obtener nombre real
        # Por ahora, devolvemos None
        return None

    def _generate_msg_id(self) -> str:
        """Genera un ID de mensaje en formato hex de 32 caracteres."""
        import hashlib
        return hashlib.md5(util.generate_token(16).encode()).hexdigest()

    @property
    def token(self) -> str:
        return self._token

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
        super().request_code(self.phone_number)

    def validate_code(self, code: str) -> None:
        self.password = super().validate_code(self.phone_number, code)

    # ================================================================
    #  MÉTODOS DE ENVÍO (CON RESOLUCIÓN AUTOMÁTICA)
    # ================================================================

    def send_message(self, target: str, body: str, msg_id: str = "") -> str:
        """Envía mensaje de texto a cualquier destino (teléfono, JID, grupo)."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = msg_id or self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_message(resolved['jid'], body, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.message(resolved['jid'], body, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def edit_message(self, target: str, new_body: str, original_msg_id: str) -> str:
        """Edita un mensaje en cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        edit_id = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_edit_message(resolved['jid'], new_body, original_msg_id, edit_id=edit_id)
        elif resolved['type'] == 'private':
            stanza_str = stanza.edit_message(resolved['jid'], new_body, original_msg_id, edit_id=edit_id)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return edit_id

    def send_file_message(self, target: str, url: str, file_type: FileType, 
                          caption: str = "", file_name: str = "", file_size: int = 0) -> str:
        """Envía archivo a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_file_message(resolved['jid'], url, file_name, file_size, caption, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.file_message(resolved['jid'], url, int(file_type), caption, msg_id=mid,
                                             file_name=file_name, file_size=file_size)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_image_message(self, target: str, url: str, file_name: str, file_size: int,
                           width: int = 0, height: int = 0, thumbnail: str = "", caption: str = "") -> str:
        """Envía imagen a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_image_message(resolved['jid'], url, file_name, file_size,
                                                    width, height, thumbnail, caption, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.image_message(resolved['jid'], url, file_name, file_size,
                                              width, height, thumbnail, caption, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_image_message_simple(self, target: str, url: str, file_name: str, file_size: int) -> str:
        """Envía imagen simple (sin metadata) a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_image_message(resolved['jid'], url, file_name, file_size, 0, 0, "", "", msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.image_message_simple(resolved['jid'], url, file_name, file_size, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_button_message(self, target: str, text: str, buttons: list[dict]) -> str:
        """Envía mensaje con botones interactivos."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            # Los botones no están soportados oficialmente en grupos, se envía como texto plano
            stanza_str = stanza.group_message(resolved['jid'], text, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.button_message(resolved['jid'], text, buttons, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_contact_message(self, target: str, contact_id: str, contact_name: str, contact_phone: str) -> str:
        """Envía contacto a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_contact_message(resolved['jid'], contact_id, contact_name, contact_phone, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.contact_message(resolved['jid'], contact_id, contact_name, contact_phone, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_sticker_message(self, target: str, sticker_id: str, sticker_name: str,
                             sticker_pack: str, sticker_hash: str) -> str:
        """Envía sticker a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_sticker_message(resolved['jid'], sticker_id, sticker_name,
                                                      sticker_pack, sticker_hash, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.sticker_message(resolved['jid'], sticker_id, sticker_name,
                                                sticker_pack, sticker_hash, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_video_message(self, target: str, url: str, video_id: str, file_name: str,
                           file_size: int, duration: int, width: int, height: int,
                           thumbnail: str, info_text: str = "") -> str:
        """Envía video a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_video_message(resolved['jid'], url, video_id, file_name, file_size,
                                                    duration, width, height, thumbnail, info_text, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.video_message(resolved['jid'], url, video_id, file_name, file_size,
                                              duration, width, height, thumbnail, msg_id=mid, info_text=info_text)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_location_message(self, target: str, lat: float, lon: float,
                              zoom: float = 11.0, text: str = "") -> str:
        """Envía ubicación a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_location_message(resolved['jid'], lat, lon, zoom, text, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.location_message(resolved['jid'], lat, lon, zoom, text, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_event_message(self, target: str, title: str, start: int, end: int,
                           all_day: bool, ics_data: str, event_id: str = "") -> str:
        """Envía evento a cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_event_message(resolved['jid'], event_id, title, start, end,
                                                    all_day, ics_data, msg_id=mid)
        elif resolved['type'] == 'private':
            stanza_str = stanza.event_message(resolved['jid'], event_id, title, start, end,
                                              all_day, ics_data, msg_id=mid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_chat_state(self, target: str, state: str) -> None:
        """Envía estado de chat (escribiendo, pausado, etc.)."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        if resolved['type'] == 'group':
            return  # No aplica a grupos
        elif resolved['type'] == 'private':
            stanza_str = stanza.chat_state(resolved['jid'], state)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())

    def delete_message(self, target: str, message_id: str, body: str = "", media_xml: str = "") -> str:
        """Elimina un mensaje en cualquier destino."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        mid = self._generate_msg_id()
        
        if resolved['type'] == 'group':
            stanza_str = stanza.group_delete_message(resolved['jid'], message_id, msg_id=mid, body=body, media_xml=media_xml)
        elif resolved['type'] == 'private':
            stanza_str = stanza.delete_message(resolved['jid'], message_id, msg_id=mid, body=body, media_xml=media_xml)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return mid

    def send_read_receipt(self, target: str, msg_id: str) -> str:
        """Envía confirmación de lectura."""
        if not self._token:
            raise AuthenticationError("No autenticado")
        
        resolved = util.resolve_target(target)
        if resolved['type'] == 'group':
            return ""  # Los grupos no usan recibos de lectura
        elif resolved['type'] == 'private':
            rid = self._generate_msg_id()
            stanza_str = stanza.read_receipt(resolved['jid'], msg_id, receipt_id=rid)
        else:
            raise ValueError(f"No se pudo resolver el destino: {target}")
        
        with self._xmpp_session(self._token) as sock:
            sock.send(stanza_str.encode())
        return rid

    # ================================================================
    #  ARCHIVOS Y PERFIL (sin cambios)
    # ================================================================

    def reserve_upload_url(self, size: int, file_type: FileType, file_name: str = "") -> tuple[str, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().reserve_upload_url(self._token, size, file_type, file_name=file_name)

    def get_real_download_url(self, url: str) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().get_real_download_url(self._token, url)

    def upload_file(self, data: bytes, file_type: FileType = FileType.FILE, 
                    progress_callback: Callable[[int, int], None] = None, file_name: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().upload_file(self._token, data, file_type, progress_callback, file_name=file_name)

    def download_file(self, url: str, path: str) -> int:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().download_file(self._token, url, path)

    def download_file_to_folder(self, url: str, folder: str, filename: str = "") -> tuple[int, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().download_file_to_folder(self._token, url, folder, filename)

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