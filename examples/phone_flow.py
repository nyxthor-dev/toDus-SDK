"""Ejemplo: flujo de registro por SMS + login y guardar token localmente."""
from todus import ToDusClient2


def main():
    phone = input("Número (ej: 5312345678): ")
    client = ToDusClient2(phone_number=phone)

    # Pedir código por SMS
    client.request_code()
    code = input("Ingresa el código recibido por SMS: ")

    # Validar código (esto asigna client.password internamente)
    client.validate_code(code)

    # Hacer login y guardar token
    try:
        client.login()
        token = client.token
        if token:
            with open("todus_token.txt", "w") as f:
                f.write(token)
            print("Login exitoso. Token guardado en todus_token.txt")
        else:
            print("Login no devolvió token")
    except Exception as e:
        print("Error durante el login:", e)


if __name__ == "__main__":
    main()
