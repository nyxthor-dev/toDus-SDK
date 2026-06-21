"""Ejemplo: bot stateful que hace login y escucha mensajes, imprimiéndolos."""
from todus import ToDusClient2


def main():
    phone = input("Número (ej: 5312345678): ")
    password = input("Password (o deja vacío si usarás validate_code() antes): ")

    client = ToDusClient2(phone_number=phone, password=password)
    if not client.logged:
        try:
            # Si no hay token, intenta hacer login (lanza si no hay password)
            client.login()
        except Exception as e:
            print("No se pudo loguear automáticamente:", e)
            code = input("Si tienes código SMS, ingrésalo ahora (enter para cancelar): ")
            if code:
                client.validate_code(code)
                client.login()

    def cb(msg: dict):
        print("Nuevo mensaje:", msg.get("from"), msg.get("id"), msg.get("body"))

    try:
        print("Escuchando mensajes... Ctrl+C para salir")
        client.listen_messages(cb)
    except KeyboardInterrupt:
        print("Saliendo")
    except Exception as e:
        print("Error en escucha:", e)


if __name__ == "__main__":
    main()
