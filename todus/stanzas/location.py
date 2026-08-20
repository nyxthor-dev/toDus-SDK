"""Generadores de stanzas para Ubicación (Location/Near) de ToDus."""

from .utils import build_iq

LOCATION_JID = "near@near.im.todus.cu"

def set_location(lat: float, lon: float) -> str:
    """Comparte tu ubicación."""
    query = f"<query xmlns='tnearp:loc:set' lat='{lat}' lon='{lon}'/>"
    return build_iq("set", LOCATION_JID, query)

def hide_location() -> str:
    """Oculta tu ubicación."""
    query = "<query xmlns='tnearp:loc:hide'/>"
    return build_iq("set", LOCATION_JID, query)

def get_people_near(limit: int = 20, offset: int = 0) -> str:
    """Obtiene la lista de personas cerca."""
    query = f"<query xmlns='tnearp:find' limit='{limit}' offset='{offset}'/>"
    return build_iq("get", LOCATION_JID, query)

def get_near_status() -> str:
    """Obtiene tu configuración actual de visibilidad (is_show_in)."""
    query = "<query xmlns='tnearp:status:get'/>"
    return build_iq("get", LOCATION_JID, query)
