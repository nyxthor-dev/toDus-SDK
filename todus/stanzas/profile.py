def set_todus_id_iq(new_id: str, msg_id: str = "") -> str:
    """
    Genera el IQ para cambiar el @username (todus_id) del usuario.
    """
    from .utils import iq
    import hashlib
    from .. import util
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    payload = f"<query xmlns='todus:users:updatetodusid' todus_id='{util.escape_xml(new_id)}'/>"
    return iq(type_="set", iq_id=mid, payload=payload, to="im.todus.cu")
