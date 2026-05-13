class ToDusError(Exception):
    pass


class AuthenticationError(ToDusError):
    pass


class TokenExpiredError(ToDusError):
    pass


class ConnectionLostError(ToDusError):
    pass


class MessageError(ToDusError):
    pass


class UploadError(ToDusError):
    pass


class ParseError(ToDusError):
    pass


class RateLimitError(ToDusError):
    pass


class StanzaError(ToDusError):
    pass
    
