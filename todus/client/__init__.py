"""Cliente XMPP/HTTP para ToDus, unificado mediante Mixins."""

import logging
import socket
import time
import random
from base64 import b64encode
from typing import Callable
from functools import wraps

from .base import ToDusClientBase
from .auth import ToDusAuthMixin
from .message import ToDusMessageMixin
from .file import ToDusFileMixin
from .profile import ToDusProfileMixin
from .channels import ToDusChannelMixin
from .status import ToDusStatusMixin
from .privacy import ToDusPrivacyMixin
from .block import ToDusBlockMixin
from .last import ToDusLastMixin
from .location import ToDusLocationMixin
from .call import ToDusCallMixin
from ..errors import AuthenticationError, TokenExpiredError, ConnectionLostError
from ..types import FileType
from .. import util

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
    """Cliente stateless para la API de ToDus unificado."""
    pass


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

    def _authstr_from_token(self, token: str) -> tuple[str, bytes]:
        phone, authstr = super()._authstr_from_token(token)
        if not phone and self.phone_number:
            phone = util.normalize_phone(self.phone_number)
            authstr = b64encode((chr(0) + phone + chr(0) + token).encode("utf-8"))
        return phone, authstr

    def _is_group_target(self, target: str) -> bool:
        """Detecta si el target es un group_id en lugar de un teléfono."""
        if not target:
            return False
        # Los teléfonos cubanos en ToDus son 10 dígitos empezando por 53
        return not (target.isdigit() and len(target) == 10 and target.startswith("53"))

    def _require_token(self, func: Callable) -> Callable:
        """Decorator para verificar que hay token válido antes de ejecutar método."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._token:
                raise AuthenticationError("No autenticado. Ejecuta login() primero.")
            return func(*args, **kwargs)
        return wrapper

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

    # --- Mensajería Privada / Grupo (auto-detección) ---

    def send_message(self, to_phone: str, body: str, reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_message(to_phone, body, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_message(self._token, to_jid, body, reply_to_id)

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
            return self.groups.send_file(to_phone, url, file_type, caption, file_name, file_size, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_file_message(self._token, to_jid, url, file_type, caption, file_name, file_size, reply_to_id)

    def send_image_message(self, to_phone: str, url: str, file_name: str, file_size: int,
                           width: int = 0, height: int = 0, thumbnail: str = "",
                           caption: str = "", reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_image(to_phone, url, file_name, file_size, width, height, thumbnail, caption, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_image_message(self._token, to_jid, url, file_name, file_size, width, height, thumbnail, caption, reply_to_id)

    def send_image_message_simple(self, to_phone: str, url: str, file_name: str,
                                  file_size: int, reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_image(to_phone, url, file_name, file_size, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_image_message_simple(self._token, to_jid, url, file_name, file_size, reply_to_id=reply_to_id)

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
            return self.groups.send_sticker(to_phone, sticker_id, sticker_name, sticker_pack, sticker_hash, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_sticker_message(self._token, to_jid, sticker_id, sticker_name, sticker_pack, sticker_hash, reply_to_id)

    def send_video_message(self, to_phone: str, url: str, video_id: str,
                           file_name: str, file_size: int, duration: int,
                           width: int, height: int, thumbnail: str,
                           info_text: str = "", reply_to_id: str = "") -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_video(to_phone, url, video_id, file_name, file_size, duration, width, height, thumbnail, info_text, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_video_message(self._token, to_jid, url, video_id, file_name, file_size, duration, width, height, thumbnail, info_text, reply_to_id)

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
            return self.groups.send_event(to_phone, title, start, end, all_day, ics_data, event_id, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().send_event_message(self._token, to_jid, title, start, end, all_day, ics_data, event_id, reply_to_id)

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
            return self.groups.delete_message(to_phone, message_id, body, media_xml, reply_to_id=reply_to_id)
        to_jid = util.build_jid(to_phone)
        return super().delete_message(self._token, to_jid, message_id, body=body, media_xml=media_xml, reply_to_id=reply_to_id)

    def send_read_receipt(self, to_phone: str, msg_id: str) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return ""
        to_jid = util.build_jid(to_phone)
        return super().send_read_receipt(self._token, to_jid, msg_id)

    # --- Archivos ---

    def reserve_upload_url(self, size: int, file_type: FileType, file_name: str = "") -> tuple[str, str]:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().reserve_upload_url(self._token, size, file_type, file_name=file_name)

    def get_real_download_url(self, url: str) -> str:
        if not self._token:
            raise AuthenticationError("No autenticado")
        return super().get_real_download_url(self._token, url)

    def upload_file(self, data: bytes, file_type: FileType = FileType.FILE, progress_callback: Callable[[int, int], None] = None, file_name: str = "") -> str:
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