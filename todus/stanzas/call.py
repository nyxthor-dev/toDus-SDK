"""Generadores de stanzas para Llamadas (Calls) de ToDus."""

from .utils import build_iq

TURN_JID = "xxxx@im.todus.cu"  # Generalmente el servidor TURN de ToDus

def get_turn_credentials(user_jid: str) -> str:
    """Solicita credenciales TURN para iniciar conexión P2P."""
    # ToDus usa tturn@im.todus.cu para turn, a veces. Verificamos con el TURN_JID.
    query = f"<query xmlns='todus:turn:cred' userId='{user_jid}'/>"
    return build_iq("get", "tturn@im.todus.cu", query)

def send_call_status(to_user: str, from_user: str, status: str, content: str = "") -> str:
    """
    Envía una actualización de estado de llamada (señalización).
    
    Args:
        to_user: JID destino.
        from_user: JID origen.
        status: Tipo de estado ('start', 'pickup', 'end', 'reject', etc).
        content: Información adicional (ej. SDP de WebRTC o motivo de fin).
    """
    query = (
        f"<query xmlns='todus:call:status' "
        f"to_user='{to_user}' "
        f"from_user='{from_user}' "
        f"status='{status}' "
        f"content='{content}'/>"
    )
    # En la APK usan jid.domain() o 'xxxx@im.todus.cu'
    return build_iq("set", "xxxx@im.todus.cu", query)
