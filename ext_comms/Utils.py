import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad


def pad_msg(msg: bytes) -> bytes:
    """Pad the message to make its length a multiple of AES block size."""
    padding_length = AES.block_size - len(msg) % AES.block_size
    padding = bytes([padding_length] * padding_length)  # Handle as bytes
    return msg + padding


def encrypt_msg(msg, secret_key) -> bytes:
    """
    Encrypts the input message (str or bytearray) using AES encryption in CBC mode.

    :param msg: Input message to be encrypted, can be a string or bytearray.
    :param secret_key: The secret key used for encryption.
    :return: The base64-encoded encrypted message as bytes.
    """
    if isinstance(msg, str):  # Convert str to bytes
        msg = msg.encode('utf-8')
    elif isinstance(msg, bytearray):
        msg = bytes(msg)

    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad_msg(msg))
    encoded = base64.b64encode(iv + encrypted_data)
    return encoded


def decrypt_message(secret_key, cipher_text, return_bytes=False):
    """
    Decrypts the input cipher_text and returns the original message as a str or bytearray.

    :param secret_key: The secret key used for decryption.
    :param cipher_text: The encrypted message in base64 format.
    :param return_bytes: Boolean flag to return the result as bytes instead of a string.
    :return: The decrypted message as a string (default) or bytearray (if return_bytes is True).
    """
    try:
        # Decode the base64-encoded cipher text into bytes
        decoded_message = base64.b64decode(cipher_text)

        # Extract the initialization vector (IV)
        iv = decoded_message[:AES.block_size]
        secret_key = secret_key.encode('utf-8')  # Convert the secret key to bytes

        # Initialize the AES cipher in CBC mode with the IV
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)

        # Decrypt the message (skip the IV part)
        decrypted_message = cipher.decrypt(decoded_message[AES.block_size:])

        # Unpad the message
        decrypted_message = unpad(decrypted_message, AES.block_size)

        if return_bytes:
            return bytearray(decrypted_message)  # Return as bytearray if requested
        else:
            # Attempt to decode as UTF-8, but handle decoding errors gracefully
            try:
                return decrypted_message.decode('utf-8')
            except UnicodeDecodeError:
                print("Warning: Decrypted message is not valid UTF-8. Returning as raw bytes.")
                return decrypted_message  # Return as bytes if it's not a valid UTF-8 string
    except Exception as e:
        print("Exception in decrypt_message: ", e)
        return "" if not return_bytes else bytearray()
