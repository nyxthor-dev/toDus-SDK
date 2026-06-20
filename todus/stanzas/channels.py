from .utils import iq
from .. import util

def create_channel_iq(name: str, link: str, public: int = 1, desc: str = "", picture: str = "", subs: list[str] = None, msg_id: str = "") -> str:
    """
    Genera el IQ para crear un nuevo canal.
    
    Args:
        name: Nombre del canal.
        link: Enlace único (sin @).
        public: 1 si es público, 0 si es privado.
        desc: Descripción del canal.
        picture: URL de la foto de perfil (previamente subida).
        subs: Lista de números (sin +) a suscribir inicialmente.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    attrs = []
    if name: attrs.append(f"name='{util.escape_xml(name)}'")
    if picture: attrs.append(f"profile_photo='{util.escape_xml(picture)}'")
    if link: attrs.append(f"link='{util.escape_xml(link)}'")
    attrs.append(f"public='{public}'")
    if subs: attrs.append(f"subs='{util.escape_xml(','.join(subs))}'")
    if desc: attrs.append(f"desc='{util.escape_xml(desc)}'")
    
    attr_str = " ".join(attrs)
    payload = f"<query xmlns='todus:ch:create' {attr_str}/>"
    return iq(type_="set", iq_id=mid, payload=payload, to="ch")

def publish_to_channel_iq(channel_jid: str, publ_xml: str, msg_id: str = "") -> str:
    """
    Genera el IQ para publicar un mensaje en un canal.
    
    Args:
        channel_jid: El JID del canal (ej. mychannel@ch.todus.cu) o el link del canal.
        publ_xml: El XML completo de la stanza `<message>` a publicar.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    if "@" not in channel_jid:
        channel_jid = f"{channel_jid}@ch.todus.cu"
        
    payload = f"<query xmlns='todus:ch:publish' publ='{util.escape_xml(publ_xml)}'/>"
    return iq(type_="set", iq_id=mid, payload=payload, to=channel_jid)

def subscribe_channel_iq(channel_jid: str, msg_id: str = "") -> str:
    """
    Genera el IQ para suscribirse a un canal.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    if "@" not in channel_jid:
        channel_jid = f"{channel_jid}@ch.todus.cu"
        
    payload = f"<query xmlns='todus:ch:subscribe'/>"
    return iq(type_="set", iq_id=mid, payload=payload, to=channel_jid)

def leave_channel_iq(channel_jid: str, msg_id: str = "") -> str:
    """
    Genera el IQ para salir de un canal.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    if "@" not in channel_jid:
        channel_jid = f"{channel_jid}@ch.todus.cu"
        
    payload = f"<query xmlns='todus:ch:leave'/>"
    return iq(type_="set", iq_id=mid, payload=payload, to=channel_jid)

def get_channel_publications_iq(channel_jid: str, last_id: str = "", limit: int = 25, msg_id: str = "") -> str:
    """
    Genera el IQ para recuperar las publicaciones de un canal.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    if "@" not in channel_jid:
        channel_jid = f"{channel_jid}@ch.todus.cu"
        
    attrs = []
    if last_id: attrs.append(f"last_id='{util.escape_xml(last_id)}'")
    if limit: attrs.append(f"limit='{limit}'")
    
    attr_str = " ".join(attrs) if attrs else ""
    payload = f"<query xmlns='todus:ch:getpub' {attr_str}/>"
    return iq(type_="get", iq_id=mid, payload=payload, to=channel_jid)

def get_my_channels_iq(msg_id: str = "") -> str:
    """
    Genera el IQ para listar los canales del usuario actual.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    payload = f"<query xmlns='todus:ch:my_channels:2'/>"
    return iq(type_="get", iq_id=mid, payload=payload, to="ch")

def get_channel_info_iq(channel_link: str, msg_id: str = "") -> str:
    """
    Genera el IQ para obtener información de un canal mediante su enlace.
    """
    import hashlib
    mid = msg_id or hashlib.md5(util.generate_token(16).encode()).hexdigest()
    
    payload = f"<query xmlns='todus:ch:info:link:v2' link='{util.escape_xml(channel_link)}'/>"
    return iq(type_="get", iq_id=mid, payload=payload, to="ch")
