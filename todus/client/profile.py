import requests
from ..types import FileType


class ToDusProfileMixin:
    """Mixin que contiene los métodos de manejo de perfil y avatar de ToDus."""

    # --- Perfil ---

    def update_profile(self, token: str, alias: str = "", bio: str = "", picture_url: str = "", thumbnail_url: str = "") -> bool:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }
        payload = {
            "alias": alias,
            "description": bio,
            "picture_url": picture_url,
            "picture_thumbnail_url": thumbnail_url,
        }
        try:
            resp = self.session.post(
                "https://auth.todus.cu/v2/todus/users.me.json",
                json=payload,
                headers=headers,
                timeout=30,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def upload_avatar(self, token: str, image_data: bytes, thumbnail_data: bytes = None) -> tuple[str, str]:
        if thumbnail_data is None:
            thumbnail_data = image_data

        up_url, down_url = self.reserve_upload_url(token, len(image_data), FileType.PROFILE)
        resp = requests.put(
            up_url,
            data=image_data,
            headers={"Content-Length": str(len(image_data)), "Content-Type": "application/octet-stream"},
            timeout=60,
        )
        resp.raise_for_status()
        profile_url = down_url

        up_url, down_url = self.reserve_upload_url(token, len(thumbnail_data), FileType.PROFILE_THUMBNAIL)
        resp = requests.put(
            up_url,
            data=thumbnail_data,
            headers={"Content-Length": str(len(thumbnail_data)), "Content-Type": "application/octet-stream"},
            timeout=60,
        )
        resp.raise_for_status()
        thumbnail_url = down_url

        return profile_url, thumbnail_url
