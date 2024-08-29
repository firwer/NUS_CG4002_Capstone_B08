import asyncio
import base64
import string
import time
from socket import *
from Utils import encrypt_msg, decrypt_msg

class WebSockController:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    secret_key: string
    ip: string
    port: int

    def __init__(self, ip, port, secret_key):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            print(f"Connected to {self.ip}:{self.port}!")
        except Exception as err:
            print(f"Error while connecting to the server: {err}. Retrying...")
            await self.reconnect()

    # Send a hello message to the evaluation server to initiate the handshake
    async def init_handshake(self):
        if not self.writer:
            print("Connection not established. Exiting...")
            return
        data = encrypt_msg("hello", self.secret_key)
        self.writer.write(f"{len(data)}_".encode())
        self.writer.write(data)
        await self.writer.drain()  # Ensure the data is sent
        print("Successfully initiated handshake with evaluation server!")

    async def reconnect(self):
        reconnect_delay = 1
        max_reconnect_attempts = 5
        attempt = 0

        while attempt < max_reconnect_attempts:
            print(f"Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
            try:
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
                print("Reconnected successfully!")
                return
            except Exception as err:
                print(f"Reconnect attempt {attempt+1} failed: {err}")
            reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff
            attempt += 1

        print("Max reconnect attempts reached. Exiting...")

    async def send(self, message):
        data = encrypt_msg(message, self.secret_key)
        self.writer.write(f"{len(data)}_".encode())
        self.writer.write(data)
        await self.writer.drain()  # Ensure the data is sent
        print(f"Sent message: {message}")

    async def receive(self):
        received_msg = await self.reader.read(2048)  # Adjust buffer size as needed
        return received_msg.decode()

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        print("Connection closed")