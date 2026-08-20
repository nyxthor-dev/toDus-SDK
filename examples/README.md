# Examples

- `jwt_connect.py`: ejemplo stateless que usa un token JWT para enviar un mensaje.
- `phone_flow.py`: solicita código por SMS, valida y realiza login, guarda token en `todus_token.txt`.
- `listen_bot.py`: bot stateful que muestra mensajes entrantes.

Notas:
- Los ejemplos son demostrativos y requieren credenciales válidas/servidor ToDus accesible.
- Para depurar handshake XMPP activa logging del logger `todus`.
