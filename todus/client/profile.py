import requests
from ..types import FileType


class ToDusProfileMixin:
    """Mixin que contiene los métodos de manejo de perfil y avatar de ToDus."""

    # --- Perfil ---

    def update_profile(self, token: str, alias: str = "", bio: str = "", picture_url: str = "", thumbnail_url: str = "") -> bool:
        def encode_varint(value: int) -> bytes:
            result = bytearray()
            while True:
                byte = value & 0x7F
                value >>= 7
                if value:
                    result.append(byte | 0x80)
                else:
                    result.append(byte)
                    break
            return bytes(result)

        def build_map_entry(key: str, value: str) -> bytes:
            key_bytes = key.encode("utf-8")
            value_bytes = value.encode("utf-8")
            entry = bytearray()
            entry.append(0x0A)
            entry.extend(encode_varint(len(key_bytes)))
            entry.extend(key_bytes)
            entry.append(0x12)
            entry.extend(encode_varint(len(value_bytes)))
            entry.extend(value_bytes)
            result = bytearray()
            result.append(0x0A)
            result.extend(encode_varint(len(entry)))
            result.extend(entry)
            return bytes(result)

        headers = {
            "Authorization": token,
            "User-Agent": "ToDus 2.1.2 Auth",
            "Content-Type": "application/x-protobuf",
        }
        
        payload = bytearray()
        if alias:
            payload.extend(build_map_entry("alias", alias))
        if bio:
            payload.extend(build_map_entry("description", bio))
        if picture_url:
            payload.extend(build_map_entry("picture_url", picture_url))
        if thumbnail_url:
            payload.extend(build_map_entry("picture_thumbnail_url", thumbnail_url))
            
        if not payload:
            return False

        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/todus/users.me",
                data=bytes(payload),
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            import logging
            logging.error(f"Error updating profile: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(e.response.text)
            return False

    def set_todus_id(self, new_id: str, msg_id: str = "") -> str:
        """
        Cambia el identificador único (@username o todus_id) de la cuenta a través de XMPP.
        El identificador no debe contener espacios ni el prefijo '@'.
        Retorna el msg_id de la petición.
        """
        if not self.logged or not self.token:
            from ..errors import AuthenticationError
            raise AuthenticationError("Se requiere haber iniciado sesión (login).")

        from ..stanzas.profile import set_todus_id_iq
        import hashlib
        from .. import util
        
        mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
        iq_xml = set_todus_id_iq(new_id, msg_id=mid)

        with self._xmpp_session(self.token) as sock:
            sock.send(iq_xml.encode())
            
        return mid

    def upload_avatar(self, token: str, image_data: bytes, thumbnail_data: bytes = None) -> tuple[str, str]:
        if thumbnail_data is None:
            thumbnail_data = image_data

        from .file import ToDusFileMixin
        from ..types import FileType
        
        up_url, down_url = ToDusFileMixin.reserve_upload_url(self, token, len(image_data), FileType.PROFILE)
        resp = self.session.put(
            up_url,
            data=image_data,
            headers={"Content-Length": str(len(image_data)), "Content-Type": "application/octet-stream"},
            timeout=60,
        )
        resp.raise_for_status()
        profile_url = down_url

        up_url, down_url = ToDusFileMixin.reserve_upload_url(self, token, len(thumbnail_data), FileType.PROFILE_THUMBNAIL)
        resp = self.session.put(
            up_url,
            data=thumbnail_data,
            headers={"Content-Length": str(len(thumbnail_data)), "Content-Type": "application/octet-stream"},
            timeout=60,
        )
        resp.raise_for_status()
        thumbnail_url = down_url

        return profile_url, thumbnail_url
