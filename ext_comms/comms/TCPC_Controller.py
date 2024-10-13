import asyncio

import config
from Utils import encrypt_msg, decrypt_message


class TCPC_Controller:
    """
        This class is responsible for the TCP Client communication for Relay Node <-> U96 & Ultra96 <-> Eval
        TCP Client will attempt to reconnect to the TCP Server using exponential retry mechanism
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
            print(f"Connected to {self.ip}:{self.port}")
        except Exception as err:
            print(f"Error while connecting to server: {err}")
            await self.reconnect()

    async def reconnect(self):
        reconnect_delay = config.FIRST_RECONNECT_DELAY
        attempt = 0
        while attempt < config.MAX_RECONNECT_COUNT:
            print(f"Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
            try:
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
                print("Reconnected successfully!")
                return
            except Exception as err:
                print(f"Reconnect attempt {attempt + 1} failed: {err}")
            reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff
            attempt += 1
        print("Max reconnect attempts reached. Exiting...")

    # Eval Client: Send a hello message to the evaluation server to initiate the handshake
    async def init_handshake(self):
        if not self.writer:
            print("Connection not established. Exiting...")
            return
        data = encrypt_msg("hello", self.secret_key)
        self.writer.write(f"{len(data)}_".encode())
        self.writer.write(data)
        await self.writer.drain()  # Ensure the data is sent
        print("Successfully initiated handshake with evaluation server!")

    # Relay Node: Send a hello packet to the TCP server to identify itself

    async def identify_relay_node(self, player_number):
        if not self.writer:
            print("Connection not established. Exiting...")
            return
        length = len(str(player_number))
        self.writer.write(f"{length}_".encode() + str(player_number).encode())
        await self.writer.drain()
        print("Successfully identified player relay node with TCP server!")

    async def send(self, message):
        encrypted_message = encrypt_msg(message, self.secret_key)
        length = len(encrypted_message)
        self.writer.write(f"{length}_".encode() + encrypted_message)
        await self.writer.drain()
        print(f"Sent message: {message}")

    async def send_no_encrypt(self, message):
        length = len(message)
        self.writer.write(f"{length}_".encode() + message)
        await self.writer.drain()
        print(f"Sent message: {message}")

    async def recv(self):
        """
        Receive a message from the TCP server.
        Used for: TCP Communication between U96 and Evaluation Server (Eval msg doesn't need to decrypt)
        :return: The received message.
        """

        data = b''
        while not data.endswith(b'_'):
            chunk = await self.reader.read(1)
            if not chunk:
                return None
            data += chunk
        length = int(data[:-1].decode())
        message = await self.reader.readexactly(length)
        return message.decode()

    async def recv_decrypt(self):
        """
        Receive a message from the TCP server and decrypt it.
        Used for: TCP Communication between Relay Node and U96
        :return: The decrypted message.
        """
        data = b''
        while not data.endswith(b'_'):
            chunk = await self.reader.read(1)
            if not chunk:
                return None
            data += chunk
        length = int(data[:-1].decode())
        message = await self.reader.readexactly(length)
        decrypted_message = decrypt_message(self.secret_key, message.decode())
        return decrypted_message
