"""Generadores de stanzas para Estados (Status/Stories) de ToDus."""

from .utils import build_iq

STATUS_JID = "status@status.im.todus.cu"

def publish_status(json_content_b64: str) -> str:
    """Publica un nuevo estado."""
    query = f"<query xmlns='td:status:publish' content='{json_content_b64}'/>"
    return build_iq("set", STATUS_JID, query)

def delete_status(status_id: str) -> str:
    """Borra un estado por su ID."""
    query = f"<query xmlns='td:status:delete' status_id='{status_id}'/>"
    return build_iq("set", STATUS_JID, query)

def get_status(status_id: str) -> str:
    """Obtiene un estado específico."""
    query = f"<query xmlns='td:status:get' status_id='{status_id}'/>"
    return build_iq("get", STATUS_JID, query)

def follow_user(uid: str) -> str:
    """Sigue los estados de un usuario."""
    query = f"<query xmlns='td:status:follow' follow_to='{uid}'/>"
    return build_iq("set", STATUS_JID, query)

def unfollow_user(uid: str) -> str:
    """Deja de seguir los estados de un usuario."""
    query = f"<query xmlns='td:status:unfollow' unfollow_to='{uid}'/>"
    return build_iq("set", STATUS_JID, query)

def get_followers(uid: str, limit: int = 20) -> str:
    """Obtiene la lista de usuarios que siguen los estados de uid."""
    query = f"<query xmlns='td:status:followers' user_jid='{uid}' limit='{limit}'/>"
    return build_iq("get", STATUS_JID, query)

def get_following(uid: str, limit: int = 20) -> str:
    """Obtiene la lista de usuarios cuyos estados sigue uid."""
    query = f"<query xmlns='td:status:following' user_jid='{uid}' limit='{limit}'/>"
    return build_iq("get", STATUS_JID, query)

def get_follower_info(uid: str) -> str:
    """Obtiene información sobre la relación de seguimiento con un usuario."""
    query = f"<query xmlns='td:status:follower:info' user_jid='{uid}'/>"
    return build_iq("get", STATUS_JID, query)
