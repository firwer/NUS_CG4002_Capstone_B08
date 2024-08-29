import base64
import string
import time
from socket import *
from Utils import encrypt_msg, decrypt_msg


class WebSockController:
    clientSocket: socket
    secret_key: string
    ip: string
    port: int

    def __init__(self, ip, port, secret_key):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port
        self.connect()

    def connect(self):
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.settimeout(10)
        try:
            self.clientSocket.connect((self.ip, self.port))
            print(f"Connected to the {self.ip}:{self.port}!")
        except Exception as err:
            print(f"Error while connecting to the server: {err}. Retrying...")
            self.reconnect()

    # Send a hello message to the evaluation server to initiate the handshake
    def init_handshake(self):
        if not self.clientSocket:
            print("Connection not established. Exiting...")
            return
        data = encrypt_msg("hello", self.secret_key)
        self.clientSocket.send(f"{len(data)}_".encode())
        self.clientSocket.send(data)
        print("Successfully initiated handshake with evaluation server!")

    def reconnect(self):
        reconnect_delay = 1
        max_reconnect_attempts = 5
        attempt = 0

        while attempt < max_reconnect_attempts:
            print(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
            try:
                self.clientSocket.connect((self.ip, self.port))
                print("Reconnected successfully!")
                return
            except Exception as err:
                print(f"Reconnect attempt {attempt+1} failed: {err}")
            reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff
            attempt += 1

        print("Max reconnect attempts reached. Exiting...")

    def send(self, message):
        data = encrypt_msg(message, self.secret_key)
        self.clientSocket.send(f"{len(data)}_".encode())
        self.clientSocket.send(data)
        print(f"Sent message: {message}")

    def receive(self):
        receivedMsg = self.clientSocket.recv(2048)
        return receivedMsg.decode()

    def close(self):
        self.clientSocket.close()
        print("Connection closed")
