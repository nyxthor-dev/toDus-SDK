"""Generadores de stanzas XML de presencia para ToDus."""

from .. import util


def presence(status: str = "Online", priority: int = 5, show: str = "", caps: bool = True) -> str:
    """Presencia estándar para chat privado."""
    cap = ""
    if caps:
        cap = (
            "<c ver='foVtX1ZDcopvf5CM63LcnVayPRs=' "
            "node='http://www.process-one.net/en/ejabberd/' "
            "hash='sha-1' xmlns='http://jabber.org/protocol/caps'/>"
        )
    show_tag = f"<show>{show}</show>" if show else ""
    return (
        f"<presence xmlns='jc'>"
        f"<status>{util.escape_xml(status)}</status>"
        f"{show_tag}"
        f"<priority>{priority}</priority>"
        f"{cap}"
        f"</presence>"
    )


def muc_presence(group_jid: str, nickname: str) -> str:
    """Presencia para unirse a grupo MUC Light."""
    return (
        f"<presence xmlns='jc' to='{group_jid}/{nickname}'>"
        f"<x xmlns='http://jabber.org/protocol/muc'/>"
        f"</presence>"
    )


def muc_unavailable(group_jid: str) -> str:
    """Presencia para salir de grupo MUC Light."""
    return f"<presence xmlns='jc' to='{group_jid}' type='unavailable'/>"
