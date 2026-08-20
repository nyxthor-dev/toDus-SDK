"""Ejemplo: uso stateless con token JWT para enviar un mensaje y escuchar."""
from todus import ToDusClient


def main():
    # Cliente stateless: pasas el token en cada llamada
    client = ToDusClient()
    token = "YOUR_JWT_TOKEN_HERE"
    to_jid = "5312345678@im.todus.cu"

    # Enviar mensaje (requiere que el token sea válido en el servidor XMPP)
    try:
        msg_id = client.send_message(token, to_jid, "Hola desde ejemplo JWT")
        print("Mensaje enviado, id:", msg_id)
    except Exception as e:
        print("Fallo al enviar mensaje:", e)


if __name__ == "__main__":
    main()
