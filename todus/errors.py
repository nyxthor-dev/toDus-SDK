"""Excepciones de ToDus."""


class ToDusError(Exception):
    """Base para todos los errores de ToDus."""


class AuthenticationError(ToDusError):
    """Credenciales inválidas o sesión expirada."""


class TokenExpiredError(ToDusError):
    """El token JWT ya no es válido."""


class ConnectionLostError(ToDusError):
    """Conexión XMPP perdida inesperadamente."""


class MessageError(ToDusError):
    """Error al enviar o recibir mensaje."""


class UploadError(ToDusError):
    """Error en subida/descarga de archivo."""


class ParseError(ToDusError):
    """Error parseando stanza XMPP."""


class RateLimitError(ToDusError):
    """Demasiadas peticiones en poco tiempo."""


class StanzaError(ToDusError):
    """Stanza malformada o no soportada."""
