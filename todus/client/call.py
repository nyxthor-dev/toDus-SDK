"""Mixin para interacciones de Llamadas de ToDus."""

from ..stanzas import call
from .. import util

class ToDusCallMixin:
    """Mixin que añade capacidades de Señalización de Llamadas a los clientes ToDus."""

    def get_turn_credentials(self, phone_number: str) -> str:
        """Solicita credenciales al servidor TURN para iniciar la transmisión de audio/video."""
        jid = util.build_jid(phone_number)
        stanza = call.get_turn_credentials(jid)
        return self.send_stanza(stanza)

    def _send_call_signal(self, phone_number: str, status: str, content: str = "") -> str:
        """Helper interno para enviar una señal de llamada."""
        to_user = util.build_jid(phone_number)
        from_user = self.jid
        stanza = call.send_call_status(to_user, from_user, status, content)
        return self.send_stanza(stanza)

    def start_call(self, phone_number: str, content: str = "") -> str:
        """Inicia la señalización de una llamada hacia un usuario."""
        return self._send_call_signal(phone_number, "start", content)

    def end_call(self, phone_number: str, reason: str = "") -> str:
        """Finaliza o cuelga una llamada."""
        return self._send_call_signal(phone_number, "end", reason)

    def pickup_call(self, phone_number: str, content: str = "") -> str:
        """Responde a una llamada entrante."""
        return self._send_call_signal(phone_number, "pickup", content)

    def reject_call(self, phone_number: str) -> str:
        """Rechaza una llamada entrante."""
        return self._send_call_signal(phone_number, "reject", "")
