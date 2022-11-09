from cryptography.fernet import Fernet
from os import path
import os

if __name__ == "__main__":
    # === Decrypt
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

    # === Wait for user to complete edits
    print("Please make the edits to 'secrets.json' now")
    input("Press enter when edits are saved.\n>> ")

    # === Re-Encrypt
    try:
        # create new key if necessary
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
    except Exception as e:
        print(e)
        print("Edit failed, please fix the issue and try again")

    os.remove("secrets.json")
