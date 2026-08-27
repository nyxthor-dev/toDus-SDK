"""Constantes del protocolo ToDus."""

XMPP_HOST = "im.todus.cu"
# Puerto XMPP de producción.
XMPP_PORT = 1756
# Puerto alternativo de producción.
XMPP_PORT_PROD2 = 5443
# Puerto XMPP clásico (obsoleto en producción, útil para entornos de prueba).
XMPP_PORT_LEGACY = 5222
MUCLIGHT_HOST = "muclight.im.todus.cu"
CHANNELS_HOST = "ch.im.todus.cu"
AUTH_VERSION_NAME = "2.1.2"
AUTH_VERSION_CODE = "30102"
BUFFER_SIZE = 1024 * 1024
# Intervalo de keepalive del cliente oficial: 30 segundos.
KEEPALIVE_INTERVAL = 30
DEFAULT_TIMEOUT = 15
