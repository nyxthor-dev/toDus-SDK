"""Generadores de stanzas para Privacidad de ToDus."""

from .utils import build_iq

PRIVACY_JID = "privacy@privacy.im.todus.cu"
GROUP_PRIVACY_JID = "privacy@groups.im.todus.cu"

def get_profile_privacy() -> str:
    """Obtiene la configuración de privacidad de perfil."""
    query = "<query xmlns='todus:privacy'/>"
    return build_iq("get", PRIVACY_JID, query)

def set_profile_privacy(profile_photo: str = "everyone", last: str = "everyone", info: str = "everyone") -> str:
    """
    Configura la privacidad de perfil.
    Valores comunes (deducidos): 'everyone', 'contacts', 'nobody'.
    """
    query = f"<query xmlns='todus:privacy' profile_photo='{profile_photo}' last='{last}' info='{info}'/>"
    return build_iq("set", PRIVACY_JID, query)

def get_group_privacy() -> str:
    """Obtiene la configuración de quién te puede añadir a grupos."""
    query = "<query xmlns='todus:group:privacy'/>"
    return build_iq("get", GROUP_PRIVACY_JID, query)

def set_group_privacy(who_can: str = "everyone", exceptions: str = "") -> str:
    """
    Configura quién te puede añadir a grupos.
    """
    query = f"<query xmlns='todus:group:privacy' who_can='{who_can}' exceptions='{exceptions}'/>"
    return build_iq("set", GROUP_PRIVACY_JID, query)
