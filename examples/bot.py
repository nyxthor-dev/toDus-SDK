"""Bot de ejemplo para ToDus con comando /start.

Uso:
    python bot.py

Configura tus credenciales en las variables de entorno:
    TODUS_PHONE=535xxxxxxx
    TODUS_PASSWORD=tu_password
"""

import os
import logging
from todus import ToDusClient2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")


def main():
    phone = os.getenv("TODUS_PHONE")
    password = os.getenv("TODUS_PASSWORD")

    if not phone or not password:
        logger.error("Faltan TODUS_PHONE o TODUS_PASSWORD")
        return

    client = ToDusClient2(phone_number=phone, password=password)
    client.login()
    logger.info("Bot conectado como %s", phone)

    def on_message(msg: dict):
        sender = msg.get("from", "")
        body = msg.get("body", "")
        msg_id = msg.get("id", "")

        logger.info("Mensaje de %s: %s", sender, body)

        # Comando /start
        if body.strip().lower() == "/start":
            reply = (
                "¡Hola! Soy un bot de ejemplo para ToDus.

"
                "Comandos disponibles:
"
                "/start - Muestra este mensaje
"
                "/info - Información del bot
"
                "/ping - Responde pong"
            )
            client.send_message(sender, reply)
            logger.info("Respondido /start a %s", sender)
            return

        # Comando /info
        if body.strip().lower() == "/info":
            client.send_message(
                sender,
                "Bot de ejemplo usando todus-lib v1.3.0
"
                "Soporta mensajes, archivos, imágenes, videos y grupos."
            )
            return

        # Comando /ping
        if body.strip().lower() == "/ping":
            client.send_message(sender, "pong")
            return

        # Eco por defecto
        if body:
            client.send_message(sender, f"Eco: {body}")

    logger.info("Escuchando mensajes...")
    client.listen_messages(on_message)


if __name__ == "__main__":
    main()
