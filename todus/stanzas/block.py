"""Generadores de stanzas para Gestión de Bloqueos de ToDus."""

from .utils import build_iq

BLOCK_JID = "blocks@blocks.im.todus.cu"

def block_user(jid: str) -> str:
    """Bloquea a un usuario."""
    query = f"<query xmlns='todus:block:set' jid='{jid}'/>"
    return build_iq("set", BLOCK_JID, query)

def unblock_user(contact_jid: str) -> str:
    """Desbloquea a un usuario."""
    # En la APK parece usar <contact> hijo o atributo contact, lo usamos como atributo por convención
    query = f"<query xmlns='todus:block:unset:2' contact='{contact_jid}'/>"
    return build_iq("set", BLOCK_JID, query)

def get_block_list() -> str:
    """Obtiene la lista completa de bloqueados (legacy/v2)."""
    query = "<query xmlns='todus:block:get:2'/>"
    return build_iq("get", BLOCK_JID, query)

def get_block_list_paginated(limit: int = 20, offset: int = 0) -> str:
    """Obtiene la lista de bloqueados de forma paginada (v3)."""
    query = f"<query xmlns='todus:block:get:3' limit='{limit}' offset='{offset}'/>"
    return build_iq("get", BLOCK_JID, query)
