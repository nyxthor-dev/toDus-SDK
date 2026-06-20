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
    """Cliente stateful con auto-login, auto-reconnect, soporte para grupos y auto-detección de destino."""

    def __init__(self, phone_number: str, password: str = "", proxy: str | None = None, **kwargs) -> None:
        super().__init__(proxy=proxy, **kwargs)
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

    # --- Métodos auxiliares para evitar duplicación ---

    def _private_send_message(self, to_jid: str, body: str) -> str:
        return super().send_message(self._token, to_jid, body)

    def _private_edit_message(self, to_jid: str, new_body: str, original_msg_id: str) -> str:
        return super().edit_message(self._token, to_jid, new_body, original_msg_id)

    def _private_send_file_message(self, to_jid: str, url: str, file_type: FileType, caption: str, file_name: str, file_size: int) -> str:
        return super().send_file_message(self._token, to_jid, url, file_type, caption, file_name, file_size)

    def _private_send_image_message(self, to_jid: str, url: str, file_name: str, file_size: int, width: int, height: int, thumbnail: str, caption: str) -> str:
        return super().send_image_message(self._token, to_jid, url, file_name, file_size, width, height, thumbnail, caption)

    def _private_send_image_message_simple(self, to_jid: str, url: str, file_name: str, file_size: int) -> str:
        return super().send_image_message_simple(self._token, to_jid, url, file_name, file_size)

    def _private_send_contact_message(self, to_jid: str, contact_id: str, contact_name: str, contact_phone: str) -> str:
        return super().send_contact_message(self._token, to_jid, contact_id, contact_name, contact_phone)

    def _private_send_sticker_message(self, to_jid: str, sticker_id: str, sticker_name: str, sticker_pack: str, sticker_hash: str) -> str:
        return super().send_sticker_message(self._token, to_jid, sticker_id, sticker_name, sticker_pack, sticker_hash)

    def _private_send_video_message(self, to_jid: str, url: str, video_id: str, file_name: str, file_size: int, duration: int, width: int, height: int, thumbnail: str, info_text: str) -> str:
        return super().send_video_message(self._token, to_jid, url, video_id, file_name, file_size, duration, width, height, thumbnail, info_text)

    def _private_send_location_message(self, to_jid: str, lat: float, lon: float, zoom: float, text: str) -> str:
        return super().send_location_message(self._token, to_jid, lat, lon, zoom, text)

    def _private_send_event_message(self, to_jid: str, title: str, start: int, end: int, all_day: bool, ics_data: str, event_id: str) -> str:
        return super().send_event_message(self._token, to_jid, title, start, end, all_day, ics_data, event_id)

    def _private_delete_message(self, to_jid: str, message_id: str, body: str, media_xml: str) -> str:
        return super().delete_message(self._token, to_jid, message_id, body=body, media_xml=media_xml)

    def _send_to_target(self, target: str, private_fn, group_fn, *args, **kwargs):
        """
        Resuelve si target es grupo o privado y ejecuta el método correspondiente.
        private_fn: función que recibe (to_jid, *args, **kwargs)
        group_fn: función que recibe (group_id, *args, **kwargs)
        """
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(target):
            return group_fn(target, *args, **kwargs)
        else:
            to_jid = util.build_jid(target)
            return private_fn(to_jid, *args, **kwargs)

    # --- Mensajería Privada / Grupo (auto-detección) ---

    def send_message(self, to_phone: str, body: str) -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_message,
            self.groups.send_message,
            body
        )

    def edit_message(self, to_phone: str, new_body: str, original_msg_id: str) -> str:
        return self._send_to_target(
            to_phone,
            self._private_edit_message,
            self.groups.edit_message,
            new_body,
            original_msg_id
        )

    def send_file_message(self, to_phone: str, url: str, file_type: FileType, caption: str = "", file_name: str = "", file_size: int = 0) -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_file_message,
            self.groups.send_file,
            url,
            file_type,
            caption,
            file_name,
            file_size
        )

    def send_image_message(self, to_phone: str, url: str, file_name: str, file_size: int, width: int = 0, height: int = 0, thumbnail: str = "", caption: str = "") -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_image_message,
            self.groups.send_image,
            url,
            file_name,
            file_size,
            width,
            height,
            thumbnail,
            caption
        )

    def send_image_message_simple(self, to_phone: str, url: str, file_name: str, file_size: int) -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_image_message_simple,
            self.groups.send_image,
            url,
            file_name,
            file_size,
            0,  # width
            0,  # height
            "", # thumbnail
            ""  # caption
        )

    def send_button_message(self, to_phone: str, text: str, buttons: list[dict]) -> str:
        # Los botones no tienen soporte nativo en grupos; se envía solo el texto
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return self.groups.send_message(to_phone, text)
        else:
            to_jid = util.build_jid(to_phone)
            return super().send_button_message(self._token, to_jid, text, buttons)

    def send_contact_message(self, to_phone: str, contact_id: str, contact_name: str, contact_phone: str) -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_contact_message,
            self.groups.send_contact,
            contact_id,
            contact_name,
            contact_phone
        )

    def send_sticker_message(self, to_phone: str, sticker_id: str, sticker_name: str, sticker_pack: str, sticker_hash: str) -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_sticker_message,
            self.groups.send_sticker,
            sticker_id,
            sticker_name,
            sticker_pack,
            sticker_hash
        )

    def send_video_message(self, to_phone: str, url: str, video_id: str, file_name: str, file_size: int, duration: int, width: int, height: int, thumbnail: str, info_text: str = "") -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_video_message,
            self.groups.send_video,
            url,
            video_id,
            file_name,
            file_size,
            duration,
            width,
            height,
            thumbnail,
            info_text
        )

    def send_location_message(self, to_phone: str, lat: float, lon: float, zoom: float = 11.0, text: str = "") -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_location_message,
            self.groups.send_location,
            lat,
            lon,
            zoom,
            text
        )

    def send_event_message(self, to_phone: str, title: str, start: int, end: int, all_day: bool, ics_data: str, event_id: str = "") -> str:
        return self._send_to_target(
            to_phone,
            self._private_send_event_message,
            self.groups.send_event,
            title,
            start,
            end,
            all_day,
            ics_data,
            event_id
        )

    def send_chat_state(self, to_phone: str, state: str) -> None:
        # Solo privado; si es grupo, ignoramos o lanzamos error
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return  # Silenciosamente ignorar, o podrías lanzar una excepción
        super().send_chat_state(self._token, util.build_jid(to_phone), state)

    def delete_message(self, to_phone: str, message_id: str, body: str = "", media_xml: str = "") -> str:
        return self._send_to_target(
            to_phone,
            self._private_delete_message,
            self.groups.delete_message,
            message_id,
            body,
            media_xml
        )

    def send_read_receipt(self, to_phone: str, msg_id: str) -> str:
        # Solo privado
        if not self._token:
            raise AuthenticationError("No autenticado")
        if self._is_group_target(to_phone):
            return ""  # O podrías lanzar una excepción
        to_jid = util.build_jid(to_phone)
        return super().send_read_receipt(self._token, to_jid, msg_id)

    # --- Recepción de mensajes (con soporte para grupos) ---

    def listen_messages(self, callback: Callable[[dict], None]) -> None:
        if not self._token:
            raise AuthenticationError("No autenticado")

        def group_aware_callback(msg: dict):
            # Procesar mensajes de grupo
            if msg.get("type") == "gc":
                msg = self.groups.process_group_message(msg)

                # Notificar callbacks específicos del grupo
                group_id = msg.get("group_id")
                if group_id and self._group_client:
                    if group_id in self._group_client._group_callbacks:
                        for cb in self._group_client._group_callbacks[group_id]:
                            try:
                                cb(msg.copy())
                            except Exception as e:
                                logger.error(f"Error en callback de grupo: {e}")

            callback(msg)

        while True:
            try:
                super().listen_messages(self._token, group_aware_callback)
            except TokenExpiredError:
                self.login()
            except (ConnectionLostError, OSError, socket.error):
                time.sleep(15)

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