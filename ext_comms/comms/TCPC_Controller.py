# TCPC_Controller.py
import asyncio
from logger_config import setup_logger
import config
from Utils import encrypt_msg, decrypt_message

logger = setup_logger(__name__)

class TCPC_Controller:
    """
    This class handles TCP Client communication between Relay Node <-> U96 & Ultra96 <-> Eval.
    It attempts to reconnect to the TCP Server using an exponential retry mechanism.
    """

    def __init__(self, ip, port, secret_key):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            logger.info(f"Connected to {self.ip}:{self.port}")
        except Exception as err:
            logger.error(f"Error while connecting to server: {err}")
            await self.reconnect()

    async def reconnect(self):
        reconnect_delay = config.FIRST_RECONNECT_DELAY
        attempt = 0
        while attempt < config.MAX_RECONNECT_COUNT:
            logger.warning(f"Reconnecting in {reconnect_delay} seconds... (Attempt {attempt + 1}/{config.MAX_RECONNECT_COUNT})")
            await asyncio.sleep(reconnect_delay)
            try:
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
                logger.info("Reconnected successfully!")
                return
            except Exception as err:
                logger.error(f"Reconnect attempt {attempt + 1} failed: {err}")
            reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff
            attempt += 1
        logger.critical("Max reconnect attempts reached. Exiting...")
        raise ConnectionError("Failed to reconnect after maximum attempts.")

    async def init_handshake(self):
        if not self.writer:
            logger.error("Connection not established. Cannot initiate handshake.")
            return
        try:
            data = encrypt_msg("hello", self.secret_key)
            self.writer.write(f"{len(data)}_".encode())
            self.writer.write(data)
            await self.writer.drain()  # Ensure the data is sent
            logger.info("Successfully initiated handshake with evaluation server!")
        except Exception as e:
            logger.exception(f"Failed to initiate handshake: {e}")

    async def identify_relay_node(self, player_number):
        if not self.writer:
            logger.error("Connection not established. Cannot identify relay node.")
            return
        try:
            length = len(str(player_number))
            self.writer.write(f"{length}_".encode() + str(player_number).encode())
            await self.writer.drain()
            logger.info("Successfully identified player relay node with TCP server!")
        except Exception as e:
            logger.exception(f"Failed to identify relay node: {e}")

    async def send(self, message):
        if not self.writer:
            logger.error("Cannot send message. Writer is not connected.")
            return
        try:
            encrypted_message = encrypt_msg(message, self.secret_key)
            length = len(encrypted_message)
            self.writer.write(f"{length}_".encode() + encrypted_message)
            await self.writer.drain()
            logger.info(f"Sent encrypted message: {message}")
        except Exception as e:
            logger.exception(f"Failed to send encrypted message: {e}")

    async def send_no_encrypt(self, message):
        if not self.writer:
            logger.error("Cannot send message. Writer is not connected.")
            return
        try:
            length = len(message)
            self.writer.write(f"{length}_".encode() + message.encode())
            await self.writer.drain()
            logger.debug(f"Sent unencrypted message: {message}")
        except Exception as e:
            logger.exception(f"Failed to send unencrypted message: {e}")

    async def recv(self):
        """
        Receive a message from the TCP server.
        Used for: TCP Communication between U96 and Evaluation Server (Eval msg doesn't need to decrypt)
        :return: The received message.
        """
        try:
            data = b''
            while not data.endswith(b'_'):
                chunk = await self.reader.read(1)
                if not chunk:
                    logger.warning("Connection closed by server.")
                    return None
                data += chunk
            length = int(data[:-1].decode())
            message = await self.reader.readexactly(length)
            logger.debug(f"Received message: {message.decode()}")
            return message.decode()
        except asyncio.IncompleteReadError:
            logger.error("Incomplete read error. Connection may have been lost.")
            return None
        except Exception as e:
            logger.exception(f"Error receiving message: {e}")
            return None

    async def recv_decrypt(self):
        """
        Receive a message from the TCP server and decrypt it.
        Used for: TCP Communication between Relay Node and U96
        :return: The decrypted message.
        """
        try:
            data = b''
            while not data.endswith(b'_'):
                chunk = await self.reader.read(1)
                if not chunk:
                    logger.warning("Connection closed by server.")
                    return None
                data += chunk
            length = int(data[:-1].decode())
            message = await self.reader.readexactly(length)
            decrypted_message = decrypt_message(self.secret_key, message.decode())
            logger.debug(f"Received decrypted message: {decrypted_message}")
            return decrypted_message
        except asyncio.IncompleteReadError:
            logger.error("Incomplete read error during decryption. Connection may have been lost.")
            return None
        except Exception as e:
            logger.exception(f"Error receiving or decrypting message: {e}")
            return None
