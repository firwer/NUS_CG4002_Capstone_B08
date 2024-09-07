import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad


def pad_msg(msg):
    padding_length = AES.block_size - len(msg) % AES.block_size
    padding = chr(padding_length) * padding_length
    return msg + padding


def encrypt_msg(msg, secret_key) -> bytes:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_CBC, iv)
    encoded = base64.b64encode(iv + cipher.encrypt(pad_msg(msg).encode('utf-8')))
    return encoded


def decrypt_message(secret_key, cipher_text):
    """
    This function decrypts the response message received from the Ultra96 using
    the secret encryption key/ password
    Credits: Evaluation Server - By Prof Jithin
    """
    try:
        decoded_message = base64.b64decode(cipher_text)  # Decode message from base64 to bytes
        iv = decoded_message[:AES.block_size]  # Get IV value
        secret_key = bytes(str(secret_key), encoding="utf8")  # Convert secret key to bytes

        cipher = AES.new(secret_key, AES.MODE_CBC, iv)  # Create new AES cipher object

        decrypted_message = cipher.decrypt(decoded_message[AES.block_size:])  # Perform decryption
        decrypted_message = unpad(decrypted_message, AES.block_size)
        decrypted_message = decrypted_message.decode('utf8')  # Decode bytes into utf-8
    except Exception as e:
        decrypted_message = ""
        print("exception in decrypt_message: ", e)
    return decrypted_message
