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


def build_iq(type_: str, to: str, query: str) -> str:
    """Helper para construir iq con id autogenerado."""
    iq_id = util.generate_token(12)
    return iq(type_, iq_id, query, to)


def ping(ping_id: str) -> str:
    """XMPP ping (urn:xmpp:ping)."""
    return f"<iq i='{ping_id}' t='get'><ping xmlns='urn:xmpp:ping'/></iq>"


def chat_state(to: str, state: str, msg_id: str = "", msg_type: str = "c") -> str:
    """Notificación de estado de chat para ToDus (XEP-0085 ofuscado).

    El protocolo de toDus define:
    ``csc`` = composing (escribiendo), ``csp`` = paused (dejó de escribir),
    ``csa`` = active, ``csi`` = inactive, ``csg`` = gone.
    """
    mid = msg_id or _generate_msg_id()
    tags = {
        "composing": "csc",
        "paused": "csp",
        "active": "csa",
        "inactive": "csi",
        "gone": "csg",
    }
    tag = tags.get(state, "csc")
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<{tag} xmlns='uc1'/>"
        f"</m>"
    )


def receipt(to: str, msg_id: str, receipt_id: str = "", msg_type: str = "c") -> str:
    """Receipt de *entrega* (received) para ToDus.

    Protocolo de toDus: ``rd`` = recibido/entregado (received)
    (mensaje entregado al cliente) y ``dd`` = DisplayedExtension (leído).
    """
    rid = receipt_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{rid}' xmlns='jc'>"
        f"<rd xmlns='x8' i='{msg_id}'/>"
        f"</m>"
    )


def read_receipt(to: str, msg_id: str, receipt_id: str = "", msg_type: str = "c") -> str:
    """Receipt de *lectura* (displayed) para ToDus.

    ``dd`` = leído (displayed) en el protocolo oficial.
    """
    rid = receipt_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{rid}' xmlns='jc'>"
        f"<dd xmlns='x8' i='{msg_id}'/>"
        f"</m>"
    )


def ack(msg_id: str, to: str = "") -> str:
    """ACK de mensaje (elemento ``ak``).

    Nota: el protocolo oficial no tiene ningún elemento ``tdack``; el elemento
    correcto para reconocer mensajes (usado en canales) es ``ak``.
    """
    to_attr = f" to='{to}'" if to else ""
    return f"<ak xmlns='x8' i='{msg_id}'{to_attr}/>"


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


def sasl_auth(authstr: bytes) -> bytes:
    """SASL PLAIN auth. Retorna bytes para enviar directamente al socket."""
    return b"<ah xmlns='ah:ns' e='PLAIN'>" + authstr + b"</ah>"


def bind(iq_id: str, username: str = "") -> str:
    """Resource bind.

    El cliente oficial envía ``<re>md5(username)_Android</re>`` como resource
    Sin resource el servidor asigna uno aleatorio.
    """
    if username:
        resource = hashlib.md5(username.encode()).hexdigest() + "_Android"
        re_xml = f"<re>{resource}</re>"
    else:
        re_xml = ""
    return f"<iq i='{iq_id}' t='set'><b1 xmlns='x4'>{re_xml}</b1></iq>"


def mam_query(query_id: str, since: str = "", before: str = "", limit: int = 50,
              with_jid: str = "") -> str:
    """Query de Message Archive Management (XEP-0313, ``urn:xmpp:mam:1``).

    El protocolo usa el namespace estándar MAM:1 con formulario ``jabber:x:data``
    y RSM para paginación — no un namespace propietario.
    """
    fields = ""
    if with_jid:
        fields += f"<field var='with'><value>{util.escape_xml(with_jid)}</value></field>"
    if since:
        fields += f"<field var='start'><value>{since}</value></field>"
    if before:
        fields += f"<field var='end'><value>{before}</value></field>"
    x_form = ""
    if fields:
        x_form = (
            f"<x xmlns='jabber:x:data' type='form'>"
            f"<field var='FORM_TYPE' type='hidden'><value>urn:xmpp:mam:1</value></field>"
            f"{fields}"
            f"</x>"
        )
    return (
        f"<iq i='{query_id}' t='set'>"
        f"<query xmlns='urn:xmpp:mam:1' queryid='{query_id}'>"
        f"{x_form}"
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
