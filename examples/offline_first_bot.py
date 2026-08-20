"""Ejemplo: Bot offline-first con Message Queue."""

import logging
from todus.client_with_queue import ToDusClientWithQueue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("offline_bot")


def main():
    """
    Bot que intenta enviar mensajes incluso si hay falta de conexión.
    Los mensajes fallidos se reintentan automáticamente con backoff exponencial.
    """
    phone = input("Número (ej: 5312345678): ")
    password = input("Password: ")
    
    # Crear cliente con Message Queue habilitado
    client = ToDusClientWithQueue(
        phone_number=phone,
        password=password,
        enable_queue=True,
        queue_db_path=None  # Usa ~/.todus/messages.db por defecto
    )
    
    # Registrar callbacks para eventos de mensajes
    def on_delivered(msg):
        logger.info(f"✓ Entregado: {msg.msg_id} a {msg.to}")
    
    def on_read(msg):
        logger.info(f"✓✓ Leído: {msg.msg_id} a {msg.to}")
    
    def on_failed(msg):
        logger.error(f"✗ Falló: {msg.msg_id} a {msg.to} - {msg.last_error}")
    
    client.register_on_message_delivered(on_delivered)
    client.register_on_message_read(on_read)
    client.register_on_message_failed(on_failed)
    
    # Hacer login
    try:
        client.login()
        logger.info(f"Autenticado como {phone}")
    except Exception as e:
        logger.error(f"Error de autenticación: {e}")
        return
    
    # Enviar algunos mensajes
    recipients = [
        "5312345678",
        "5387654321",
    ]
    
    for recipient in recipients:
        try:
            msg_id = client.send_message_queued(recipient, f"Hola desde bot offline-first")
            logger.info(f"Mensaje encolado: {msg_id}")
        except Exception as e:
            logger.error(f"Error al enviar: {e}")
    
    # Mostrar estadísticas de la cola
    stats = client.get_queue_stats()
    logger.info(f"Estadísticas de la cola: {stats}")
    
    # Intentar escuchar mensajes
    def callback(msg):
        logger.info(f"Mensaje recibido: {msg.get('from')} - {msg.get('body')}")
        
        # Marcar como entregado en la cola
        if msg.get("id"):
            client.queue.mark_delivered(msg.get("id"))
    
    try:
        logger.info("Escuchando mensajes... (Ctrl+C para salir)")
        client.listen_messages(callback)
    except KeyboardInterrupt:
        logger.info("Saliendo...")
    finally:
        # Limpiar
        client.cleanup_queue()


if __name__ == "__main__":
    main()
