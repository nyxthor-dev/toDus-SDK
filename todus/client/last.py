"""Mixin para interacciones de Última Conexión de ToDus."""

from ..stanzas import last
from .. import util

class ToDusLastMixin:
    """Mixin que añade capacidades de consultar Última Conexión a los clientes ToDus."""

    def get_last_seen(self, phone_number: str) -> str:
        """Obtiene la última vez que un usuario estuvo conectado."""
        jid = util.build_jid(phone_number)
        stanza = last.get_last_seen(jid)
        return self.send_stanza(stanza)
