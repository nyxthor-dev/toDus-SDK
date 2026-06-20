"""Soporte para grupos MUC Light de ToDus."""

from __future__ import annotations

import logging
import re
import hashlib
import time
import socket
from typing import Callable, Optional, List, Dict, TYPE_CHECKING, Any

from . import util, constants, stanza
from .errors import AuthenticationError, ConnectionLostError, GroupError, TokenExpiredError
from .types import FileType

if TYPE_CHECKING:
    from .client import ToDusClient2

logger = logging.getLogger("todus.groups")


class GroupRole:
    """Roles en grupo MUC Light."""
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    OWNER = "owner"


class GroupEvent:
    """Eventos de grupo."""
    MEMBER_JOINED = "joined"
    MEMBER_LEFT = "left"
    MEMBER_KICKED = "kicked"
    MEMBER_BANNED = "banned"
    SUBJECT_CHANGED = "subject_changed"
    ROOM_CREATED = "created"
    ROOM_DESTROYED = "destroyed"


class GroupClient:
    """Cliente para manejo de grupos MUC Light de ToDus."""
    
    def __init__(self, parent_client: ToDusClient2):
        self.client = parent_client
        self._joined_groups: set[str] = set()
        self._group_callbacks: Dict[str, List[Callable]] = {}
        
    def _get_group_jid(self, group_id: str) -> str:
        """Construye JID del grupo."""
        return f"{group_id}@muclight.im.todus.cu"
    
    def _generate_msg_id(self) -> str:
        """Genera ID de mensaje en formato hex MD5 de 32 chars."""
        return hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    def _extract_group_info(self, stanza_dict: dict) -> tuple[str, str]:
        """Extrae group_id y sender_phone de una stanza de grupo."""
        from_jid = stanza_dict.get("from", "")
        if "@muclight.im.todus.cu" not in from_jid:
            return "", ""
        
        # group_id@muclight.im.todus.cu/sender@im.todus.cu
        parts = from_jid.split("/", 1)
        group_id = ""
        if parts:
            group_part = parts[0]
            if "@" in group_part:
                group_id = group_part.split("@")[0]
        
        sender = ""
        if len(parts) > 1:
            sender_jid = parts[1]
            if "@" in sender_jid:
                sender = sender_jid.split("@")[0]
        
        return group_id, sender
    
    # --- Acciones de grupo ---
    
    def join(self, group_id: str, nickname: str = "") -> bool:
        """Unirse a un grupo MUC Light."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        nick = nickname or self.client.phone_number
        
        presence = stanza.muc_presence(group_jid, nick)
        
        try:
            with self.client._xmpp_session(self.client.token) as sock:
                sock.send(presence.encode())
                self._joined_groups.add(group_id)
                logger.info(f"Unido al grupo: {group_id}")
                return True
        except Exception as e:
            logger.error(f"Error uniéndose al grupo {group_id}: {e}")
            raise GroupError(f"No se pudo unir al grupo: {e}")
    
    def leave(self, group_id: str, msg_id: str = "") -> bool:
        """Salir formalmente de un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
            
        if group_id not in self._joined_groups:
            # Intentamos enviar el leave de todas formas por si es un grupo del que 
            # no nos hemos unido en esta sesion pero queremos salir de verdad.
            pass
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        leave_iq = stanza.group_leave_iq(group_jid, msg_id=mid)
        
        try:
            with self.client._xmpp_session(self.client.token) as sock:
                sock.send(leave_iq.encode())
                self._joined_groups.discard(group_id)
                logger.info(f"Salido del grupo: {group_id}")
                return True
        except Exception as e:
            logger.error(f"Error saliendo del grupo {group_id}: {e}")
            return False
    
    def send_message(self, group_id: str, body: str, msg_id: str = "") -> str:
        """Enviar mensaje de texto a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_message(group_jid, body, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    def send_file(self, group_id: str, url: str, file_name: str, 
                  file_size: int, caption: str = "", msg_id: str = "") -> str:
        """Enviar archivo a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_file_message(group_jid, url, file_name, file_size, caption, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    def send_image(self, group_id: str, url: str, file_name: str,
                   file_size: int, width: int, height: int,
                   thumbnail: str = "", caption: str = "", msg_id: str = "") -> str:
        """Enviar imagen a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_image_message(group_jid, url, file_name, file_size,
                                          width, height, thumbnail, caption, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    def send_video(self, group_id: str, url: str, video_id: str,
                   file_name: str, file_size: int, duration: int,
                   width: int, height: int, thumbnail: str,
                   caption: str = "", msg_id: str = "") -> str:
        """Enviar video a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_video_message(group_jid, url, video_id, file_name,
                                          file_size, duration, width, height,
                                          thumbnail, caption, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    def send_sticker(self, group_id: str, sticker_id: str,
                     sticker_name: str, sticker_pack: str,
                     sticker_hash: str, msg_id: str = "") -> str:
        """Enviar sticker a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_sticker_message(group_jid, sticker_id, sticker_name,
                                            sticker_pack, sticker_hash, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    def send_contact(self, group_id: str, contact_id: str,
                     contact_name: str, contact_phone: str,
                     msg_id: str = "") -> str:
        """Enviar contacto a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_contact_message(group_jid, contact_id, contact_name,
                                            contact_phone, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid

    def send_location(self, group_id: str, lat: float, lon: float,
                      zoom: float = 11.0, text: str = "", msg_id: str = "") -> str:
        """Enviar ubicación a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_location_message(group_jid, lat, lon, zoom, text, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid

    def send_event(self, group_id: str, title: str, start: int, end: int,
                   all_day: bool, ics_data: str, event_id: str = "") -> str:
        """Enviar evento a un grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = self._generate_msg_id()
        
        msg = stanza.group_event_message(group_jid, event_id, title, start, end, all_day, ics_data, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid

    def set_name(self, group_id: str, name: str, msg_id: str = "") -> str:
        """Actualizar el nombre del grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_update_name(group_jid, name, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid

    def set_subject(self, group_id: str, subject: str, msg_id: str = "") -> str:
        """Actualizar el asunto o descripción del grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        msg = stanza.group_update_subject(group_jid, subject, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid

    def set_avatar(self, group_id: str, avatar_url: str, thumbnail_url: str = "", msg_id: str = "") -> str:
        """Actualizar el avatar del grupo.
        
        Típicamente requiere subir la imagen a los servidores de ToDus primero (como 'profile' o 'picture')
        y obtener las URLs de la imagen y la miniatura.
        """
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        
        # Enviar stanza de imagen original
        msg1 = stanza.group_update_avatar(group_jid, avatar_url, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg1.encode())
            
            # Enviar miniatura si está disponible (es lo que hace la app)
            if thumbnail_url:
                mid_thumb = self._generate_msg_id()
                msg2 = stanza.group_update_avatar_thumbnail(group_jid, thumbnail_url, msg_id=mid_thumb)
                sock.send(msg2.encode())
        
        return mid
    
    def get_invite_link(self, group_id: str, msg_id: str = "") -> str:
        """Solicitar el enlace de invitación del grupo.
        Retorna el msg_id de la petición. El resultado llegará por listen_messages()."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
            
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        iq_msg = stanza.group_get_link_iq(group_jid, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(iq_msg.encode())
            
        return mid

    def revoke_invite_link(self, group_id: str, msg_id: str = "") -> str:
        """Revocar el enlace actual y generar uno nuevo.
        Retorna el msg_id de la petición."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
            
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        iq_msg = stanza.group_set_link_iq(group_jid, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(iq_msg.encode())
            
        return mid

    def get_members(self, group_id: str, msg_id: str = "") -> str:
        """Solicitar la lista de miembros del grupo.
        Retorna el msg_id de la petición. El resultado llegará por listen_messages()."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
            
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        iq_msg = stanza.group_get_members_iq(group_jid, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(iq_msg.encode())
            
        return mid

    def set_member_role(self, group_id: str, user_phone: str, role: str, msg_id: str = "") -> str:
        """Modificar el rol de un miembro o añadirlo (ej. participant, moderator, owner)."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
            
        group_jid = self._get_group_jid(group_id)
        mid = msg_id or self._generate_msg_id()
        affiliations = {user_phone: role}
        iq_msg = stanza.group_set_members_iq(group_jid, affiliations, msg_id=mid)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(iq_msg.encode())
            
        return mid

    def kick_member(self, group_id: str, user_phone: str, msg_id: str = "") -> str:
        """Expulsar a un miembro del grupo (asignar rol 'none')."""
        return self.set_member_role(group_id, user_phone, "none", msg_id=msg_id)

    def edit_message(self, group_id: str, new_body: str, 
                     original_msg_id: str) -> str:
        """Editar un mensaje en grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        edit_id = self._generate_msg_id()
        
        msg = stanza.group_edit_message(group_jid, new_body, original_msg_id, edit_id)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return edit_id
    
    def delete_message(self, group_id: str, message_id: str, body: str = "", media_xml: str = "") -> str:
        """Eliminar un mensaje en grupo."""
        if not self.client.token:
            raise AuthenticationError("No autenticado")
        
        group_jid = self._get_group_jid(group_id)
        mid = self._generate_msg_id()
        
        msg = stanza.group_delete_message(group_jid, message_id, mid, body=body, media_xml=media_xml)
        
        with self.client._xmpp_session(self.client.token) as sock:
            sock.send(msg.encode())
        
        return mid
    
    # --- Recepción de mensajes de grupo ---
    
    def process_group_message(self, msg: dict) -> dict:
        """Procesa y enriquece un mensaje de grupo."""
        if msg.get("type") != "gc":
            return msg
        
        group_id, sender = self._extract_group_info(msg)
        
        msg["is_group"] = True
        msg["group_id"] = group_id
        msg["sender_phone"] = sender
        
        # Detectar eventos de grupo
        raw = msg.get("raw", "")
        if "<x xmlns='http://jabber.org/protocol/muc#user'>" in raw:
            msg["is_group_event"] = True
            msg["event"] = self._parse_group_event(raw)
        
        # Extraer subject (tema del grupo)
        if "<subject>" in raw:
            subj_match = re.search(r"<subject>(.*?)</subject>", raw)
            if subj_match:
                msg["subject"] = util.unescape_xml(subj_match.group(1))
        
        return msg
    
    def _parse_group_event(self, raw_stanza: str) -> Optional[str]:
        """Parsea eventos de grupo (entrada/salida, etc.)."""
        if "<status code='110'/>" in raw_stanza:
            return GroupEvent.MEMBER_JOINED
        if '<status code="303"/>' in raw_stanza:
            return GroupEvent.MEMBER_LEFT
        if '<status code="307"/>' in raw_stanza:
            return GroupEvent.MEMBER_KICKED
        if '<status code="301"/>' in raw_stanza:
            return GroupEvent.MEMBER_BANNED
        if "<subject" in raw_stanza and "</subject>" in raw_stanza:
            return GroupEvent.SUBJECT_CHANGED
        return None
        
    def parse_invite_link_response(self, raw_stanza: str) -> Optional[str]:
        """
        Extrae el enlace de invitación a partir de la respuesta cruda de un IQ stanza (x14).
        Útil para capturar la respuesta generada por get_invite_link() o revoke_invite_link().
        """
        if "xmlns='x14'" not in raw_stanza:
            return None
        # <query xmlns='x14'>https://todus.cu/l/xxx</query> o simplemente extraer el contenido
        link_match = re.search(r"<query xmlns='x14'>([^<]+)</query>", raw_stanza)
        if link_match:
            return util.unescape_xml(link_match.group(1))
        return None

    def parse_members_response(self, raw_stanza: str) -> Optional[Dict[str, str]]:
        """
        Extrae la lista de miembros y roles a partir de la respuesta cruda de un IQ stanza (x11).
        Retorna un diccionario de la forma: {"5350000000": "participant", ...}
        """
        if "xmlns='x11'" not in raw_stanza:
            return None
        
        members = {}
        # Buscar todas las etiquetas <user affiliation='rol'>numero@im.todus.cu</user>
        matches = re.finditer(r"<user affiliation='([^']+)'>([^<@]+)(?:@[^<]+)?</user>", raw_stanza)
        for match in matches:
            role = match.group(1)
            phone = match.group(2)
            members[phone] = role
            
        return members
    
    def on_group_message(self, group_id: str, callback: Callable):
        """Registra callback para mensajes de un grupo específico."""
        if group_id not in self._group_callbacks:
            self._group_callbacks[group_id] = []
        self._group_callbacks[group_id].append(callback)
    
    def remove_callback(self, group_id: str, callback: Callable = None):
        """Elimina callback(s) de un grupo."""
        if group_id not in self._group_callbacks:
            return
        if callback is None:
            del self._group_callbacks[group_id]
        else:
            self._group_callbacks[group_id] = [
                cb for cb in self._group_callbacks[group_id] if cb != callback
            ]
    
    # --- Utilidades ---
    
    def is_joined(self, group_id: str) -> bool:
        """Verifica si está unido a un grupo."""
        return group_id in self._joined_groups
    
    def get_joined_groups(self) -> List[str]:
        """Lista de grupos a los que está unido."""
        return list(self._joined_groups)
    
    def upload_and_send_image(self, group_id: str, image_data: bytes,
                              filename: str = "image.jpg", caption: str = "") -> str:
        """Sube una imagen y la envía al grupo en un solo paso."""
        url = self.client.upload_file(image_data, FileType.PICTURE, file_name=filename)
        width, height = util.get_image_dimensions(image_data)
        thumbnail = util.generate_blurhash(width, height)
        
        return self.send_image(
            group_id, url, filename, len(image_data),
            width, height, thumbnail, caption
        )
    
    def upload_and_send_file(self, group_id: str, file_data: bytes,
                             filename: str, caption: str = "") -> str:
        """Sube un archivo y lo envía al grupo en un solo paso."""
        url = self.client.upload_file(file_data, FileType.FILE, file_name=filename)
        return self.send_file(group_id, url, filename, len(file_data), caption)