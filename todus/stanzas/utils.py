"""Stanzas XML de utilidad y de protocolo XMPP para ToDus."""

import hashlib
from .. import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def iq(type_: str, iq_id: str, payload: str = "", to: str = "") -> str:
    """Stanza IQ genérica."""
    to_attr = f" to='{to}'" if to else ""
    return f"<iq i='{iq_id}' t='{type_}'{to_attr}>{payload}</iq>"


def ping(ping_id: str) -> str:
    """XMPP ping (urn:xmpp:ping)."""
    return f"<iq i='{ping_id}' t='get'><ping xmlns='urn:xmpp:ping'/></iq>"


def chat_state(to: str, state: str, msg_id: str = "", msg_type: str = "c") -> str:
    """Notificación de estado de chat para ToDus."""
    mid = msg_id or _generate_msg_id()
    tag = "csp" if state == "composing" else "csc"
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<{tag} xmlns='uc1'/>"
        f"</m>"
    )


def receipt(to: str, msg_id: str, receipt_id: str = "", msg_type: str = "c") -> str:
    """Delivery receipt para ToDus."""
    rid = receipt_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{rid}' xmlns='jc'>"
        f"<dd xmlns='x8' i='{msg_id}'/>"
        f"</m>"
    )


def read_receipt(to: str, msg_id: str, receipt_id: str = "", msg_type: str = "c") -> str:
    """Read receipt para ToDus."""
    rid = receipt_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{rid}' xmlns='jc'>"
        f"<rd xmlns='x8' i='{msg_id}'/>"
        f"</m>"
    )


def ack(msg_id: str, to: str = "") -> str:
    """ACK de mensaje recibido (tdack)."""
    return f"<tdack xmlns='x8' mi='{msg_id}'/>"


def keepalive() -> str:
    """Keepalive: espacio en blanco."""
    return " "


def stream_open(host: str = "im.todus.cu") -> str:
    """Stream header inicial."""
    return f"<stream:stream xmlns='jc' o='{host}' xmlns:stream='x1' v='1.0'>"


def stream_restart(host: str = "im.todus.cu") -> str:
    """Stream header post-auth."""
    return f"<stream:stream xmlns='jc' o='{host}' xmlns:stream='x1' v='1.0'>"


def stream_close() -> str:
    """Cierre graceful del stream."""
    return "</stream:stream>"


def sasl_auth(authstr: bytes) -> str:
    """SASL PLAIN auth."""
    return b"<ah xmlns='ah:ns' e='PLAIN'>" + authstr + b"</ah>"


def bind(iq_id: str) -> str:
    """Resource bind."""
    return f"<iq i='{iq_id}' t='set'><b1 xmlns='x4'></b1></iq>"


def mam_query(query_id: str, since: str = "", before: str = "", limit: int = 50) -> str:
    """Query de Message Archive Management (MAM)."""
    filters = ""
    if since:
        filters += f"<start>{since}</start>"
    if before:
        filters += f"<end>{before}</end>"
    return (
        f"<iq i='{query_id}' t='set'>"
        f"<query xmlns='todus:mam'>{filters}"
        f"<set xmlns='http://jabber.org/protocol/rsm'><max>{limit}</max></set>"
        f"</query></iq>"
    )


def upload_query(iq_id: str, size: int, file_type: int, persistent: bool = False, file_name: str = "") -> str:
    """Reserva URL de subida."""
    persist = "true" if persistent else "false"
    n_attr = f" n='{util.escape_xml(file_name)}'" if file_name else ""
    return (
        f"<iq i='{iq_id}-3' t='get'>"
        f"<query xmlns='todus:purl' type='{file_type}' "
        f"persistent='{persist}' size='{size}' room=''{n_attr}></query>"
        f"</iq>"
    )


def download_query(iq_id: str, url: str) -> str:
    """Resuelve URL real de descarga."""
    return (
        f"<iq i='{iq_id}-2' t='get'>"
        f"<query xmlns='todus:gurl' url='{url}'></query>"
        f"</iq>"
    )
