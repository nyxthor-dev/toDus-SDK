"""Mixin para interacciones de Ubicación (Near) de ToDus."""

from ..stanzas import location

class ToDusLocationMixin:
    """Mixin que añade capacidades de Ubicación a los clientes ToDus."""

    def set_location(self, lat: float, lon: float) -> str:
        """Comparte tu ubicación geográfica en el sistema 'Cerca de mí'."""
        stanza = location.set_location(lat, lon)
        return self.send_stanza(stanza)

    def hide_location(self) -> str:
        """Oculta tu ubicación para no aparecer en 'Cerca de mí'."""
        stanza = location.hide_location()
        return self.send_stanza(stanza)

    def get_people_near(self, limit: int = 20, offset: int = 0) -> str:
        """Busca personas cerca de tu ubicación actual (si está compartida)."""
        stanza = location.get_people_near(limit, offset)
        return self.send_stanza(stanza)

    def get_near_status(self) -> str:
        """Obtiene tu configuración actual de visibilidad de ubicación."""
        stanza = location.get_near_status()
        return self.send_stanza(stanza)
