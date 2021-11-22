from cryptography.fernet import Fernet
from os import path

if __name__ == "__main__":
    if not path.isfile("secrets.key"):
        key = Fernet.generate_key()
        with open('secrets.key', 'wb') as file:
            file.write(key)

    # load key
    with open('secrets.key', 'rb') as file:
        key = file.read()

    # load plain secrets
    with open('secrets.json', 'rb') as f:
        data = f.read()

    # encrypt
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)

    with open('secrets.json.enc', 'wb') as f:
        f.write(encrypted)
