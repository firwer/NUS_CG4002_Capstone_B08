import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def pad_msg(msg):
    padding_length = AES.block_size - len(msg) % AES.block_size
    padding = chr(padding_length) * padding_length
    return msg + padding


def encrypt_msg(msg, secret_key) -> bytes:
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_CBC, iv)
    encoded = base64.b64encode(iv + cipher.encrypt(pad_msg(msg).encode('utf-8')))
    return encoded


def decrypt_msg(msg, secret_key) -> str:
    decoded = base64.b64decode(msg)
    iv = decoded[:AES.block_size]
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(decoded[AES.block_size:]).decode('utf-8')
    return decrypted[:-ord(decrypted[-1])]
