import asyncio
from Utils import encrypt_msg, decrypt_message


class TCPS_Controller:
    """
        This class is responsible for the TCP Server communication for Relay Node <-> U96 (Server)

        start_server will automatically listen for incoming connections and handle them

        All received messages from client will be pushed to the receive_queue
        All messages to be sent to client will be pushed to the send_queue
    """
    def __init__(self, ip, port, secret_key, receive_queue, send_queue):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port
        self.receive_queue = receive_queue
        self.send_queue = send_queue
        self.writer = None
        self.reader = None

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, host=self.ip, port=self.port)
        print(f"Ultra96 Server started on {self.ip}:{self.port}")
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connection established with {addr}")

        self.writer = writer
        self.reader = reader
        tasks = []
        try:
            while True:
                receive_task = asyncio.create_task(self._receive_task())
                send_task = asyncio.create_task(self._send_task())
                tasks.extend([receive_task, send_task])
                # Wait for both tasks to run concurrently
                await asyncio.gather(receive_task, send_task)
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            print(f"Closing connection with {addr}")
            await self.clean_up_connection()

    async def _receive_task(self):
        """Continuously receive messages from the client and place them in the receive_queue."""
        addr = self.writer.get_extra_info('peername')
        try:
            while True:
                success, message = await self._recv_message(self.reader)
                if not success:
                    await self._send_message(self.writer, "ERROR: Malformed data received.")
                    print(f"Error in data received from {addr}. Sent error response.")
                    continue
                print(f"Received message from {addr}: {message}")
                await self.receive_queue.put(message)  # Place the received message in the queue
        except Exception as e:
            print(f"Exception in receiving messages: {e}")
            await self.clean_up_connection()

    async def _send_task(self):
        """Continuously send messages from the send_queue to the connected client."""
        try:
            while True:
                # Wait until there's a message to send
                message = await self.send_queue.get()
                await self._send_message(self.writer, message)  # Send the message to the client
        except Exception as e:
            print(f"Exception in sending messages: {e}")
            await self.clean_up_connection()

    async def _send_message(self, writer, message):
        encrypted_message = encrypt_msg(message, self.secret_key)
        length = len(encrypted_message)
        writer.write(f"{length}_".encode() + encrypted_message)
        await writer.drain()
        print(f"Sent message: {message}")

    async def _recv_message(self, reader, timeout=60):
        try:
            data = b''
            while not data.endswith(b'_'):
                chunk = await reader.read(1)
                if not chunk:
                    return False, "Relay Node's TCP Client disconnected."
                data += chunk
            length = int(data[:-1].decode())
            message = await asyncio.wait_for(reader.readexactly(length), timeout)
            return True, decrypt_message(self.secret_key, message.decode())
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ValueError):
            print("Data reception error or invalid format.")
            return False, None
        except ConnectionAbortedError:
            print("Connection aborted by Relay Node's TCP Client")
            return False, None

    async def clean_up_connection(self):
        if not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()
        print("Cleaned up connection and closed writer.")
