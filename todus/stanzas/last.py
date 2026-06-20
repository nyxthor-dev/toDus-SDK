"""Generadores de stanzas para Última Vez (Last Seen) de ToDus."""

from .utils import build_iq

def get_last_seen(jid: str) -> str:
    """Obtiene la última vez de conexión de un usuario."""
    # ToDus usa el JID del usuario como 'to' para esta consulta
    query = "<query xmlns='todus:last:2'/>"
    return build_iq("get", jid, query)
