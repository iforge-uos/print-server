from cryptography.fernet import Fernet
from os import path

if __name__ == "__main__":
    if not path.isfile("secrets.key"):
        print(f"Error, you need the key!")
    else:
        # load key
        with open('secrets.key', 'rb') as file:
            key = file.read()

        # load enc secrets
        with open('secrets.json.enc', 'rb') as f:
            data = f.read()

        # encrypt
        fernet = Fernet(key)
        decrypted = fernet.decrypt(data)

        with open('secrets.json', 'wb') as f:
            f.write(decrypted)
