"""Generadores de stanzas XML de presencia para ToDus.

Fix v1.10.2: tag ``<p>`` en vez de ``<presence>`` y atributo ``o=`` en
vez de ``to=``. Alineado con ElJoker63/toDus-API (protocolo oficial).
"""

from .. import util


def presence(status: str = "Online", priority: int = 5, show: str = "", caps: bool = True) -> str:
    """Presencia estándar para chat privado usando tag ``<p>``.

    Fix v1.10.2: el protocolo de toDus usa ``<p>`` (no ``<presence>``).
    """
    cap = ""
    if caps:
        cap = (
            "<c ver='foVtX1ZDcopvf5CM63LcnVayPRs=' "
            "node='http://www.process-one.net/en/ejabberd/' "
            "hash='sha-1' xmlns='http://jabber.org/protocol/caps'/>"
        )
    show_tag = f"<show>{show}</show>" if show else ""
    return (
        f"<p xmlns='jc'>"
        f"<status>{util.escape_xml(status)}</status>"
        f"{show_tag}"
        f"<priority>{priority}</priority>"
        f"{cap}"
        f"</p>"
    )


def muc_presence(group_jid: str, nickname: str) -> str:
    """Presencia para unirse a grupo MUC Light.

    Fix v1.10.2: tag ``<p>`` y atributo ``o=``.
    """
    return (
        f"<p xmlns='jc' o='{group_jid}/{nickname}'>"
        f"<x xmlns='http://jabber.org/protocol/muc'/>"
        f"</p>"
    )


def muc_unavailable(group_jid: str) -> str:
    """Presencia para salir de grupo MUC Light.

    Fix v1.10.2: tag ``<p>`` y atributo ``o=``.
    """
    return f"<p xmlns='jc' o='{group_jid}' type='unavailable'/>"
