"""Mixin para interacciones de Privacidad de ToDus."""

from ..stanzas import privacy

class ToDusPrivacyMixin:
    """Mixin que añade capacidades de Privacidad a los clientes ToDus."""

    def get_profile_privacy(self) -> str:
        """Obtiene la configuración de privacidad de tu perfil (foto, última vez, info)."""
        stanza = privacy.get_profile_privacy()
        return self.send_stanza(stanza)

    def set_profile_privacy(self, profile_photo: str = "everyone", last: str = "everyone", info: str = "everyone") -> str:
        """Configura la privacidad de tu perfil."""
        stanza = privacy.set_profile_privacy(profile_photo, last, info)
        return self.send_stanza(stanza)

    def get_group_privacy(self) -> str:
        """Obtiene la configuración de quién te puede añadir a grupos."""
        stanza = privacy.get_group_privacy()
        return self.send_stanza(stanza)

    def set_group_privacy(self, who_can: str = "everyone", exceptions: str = "") -> str:
        """Configura quién te puede añadir a grupos."""
        stanza = privacy.set_group_privacy(who_can, exceptions)
        return self.send_stanza(stanza)
