import asyncio
import traceback

from Utils import encrypt_msg, decrypt_message


class TCPS_Controller:
    """
        This class is responsible for the TCP Server communication for Relay Node <-> U96 (Server)

        start_server will automatically listen for incoming connections and handle them

        All received messages from client will be pushed to the receive_queue
        All messages to be sent to client will be pushed to the send_queue
    """

    def __init__(self, ip, port, secret_key, receive_queue_p1, receive_queue_p2, send_queue):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port
        self.receive_queue_p1 = receive_queue_p1
        self.receive_queue_p2 = receive_queue_p2
        self.send_queue = send_queue
        self.client_player_map = {}  # Keep track of each client's player number
        self.client_tasks = {}  # Keep track of each client tasks
        self.connected_clients = set()  # Keep track of connected clients

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, host=self.ip, port=self.port)
        print(f"Ultra96 Server started on {self.ip}:{self.port}")

        broadcast_task = asyncio.create_task(self._broadcast_task())  # Start the broadcast task
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Incoming connection from {addr}. Waiting for identification...")

        # Receive hello packet containing player number from client
        success, message = await self._recv_message(reader)
        if not success:
            print(f"Error in hello packet received from {addr}. Sent error response.")
            writer.close()
            await writer.wait_closed()
            return

        try:
            player_number = int(message.strip())
            self.client_player_map[writer] = player_number
            self.connected_clients.add(writer)
            print(f"Player {player_number} connected from {addr}")
        except ValueError:
            print(f"Invalid player number received from {addr}. Closing connection.")
            writer.close()
            await writer.wait_closed()
            return

        try:
            receive_task = asyncio.create_task(self._receive_task(reader, writer, player_number))
            self.client_tasks[writer] = (receive_task,)
            await receive_task
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            print(f"Closing connection with {addr}")
            await self.clean_up_connection(writer)

    async def _receive_task(self, reader, writer, player_number):
        """Continuously receive messages from the client and place them in the receive_queue."""
        addr = writer.get_extra_info('peername')
        try:
            while True:
                success, message = await self._recv_message(reader)
                if not success:
                    print(f"Error in data received from {addr}. Sent error response.")
                    break
                print(f"Received message from Player {player_number} ({addr}): {message}")
                if player_number == 1:
                    await self.receive_queue_p1.put(message)
                elif player_number == 2:
                    await self.receive_queue_p2.put(message)
                else:
                    print(f"Invalid player number {player_number} received from {addr}.")
        except Exception as e:
            print(f"Exception in receiving messages from {addr}: {e}")
        finally:
            await self.clean_up_connection(writer)

    async def _broadcast_task(self):
        print("TCP Server Broadcast task started.")
        """Continuously read messages from send_queue and broadcast them to all connected clients."""
        while True:
            message = await self.send_queue.get()
            print(f"Broadcasting message: {message}")
            await self.broadcast_message(message)

    async def broadcast_message(self, message):
        """Send a message to all connected clients."""
        for writer in list(self.connected_clients):
            try:
                await self._send_message(writer, message)
            except Exception as e:
                print(f"Error sending message to client: {e}")
                await self.clean_up_connection(writer)

    async def _send_message(self, writer, message):
        print(f"Sending message to Player {self.client_player_map.get(writer, 'Unknown')}: {message}")
        writer.write(f"{len(message)}_".encode() + message.encode())
        await writer.drain()
        print(f"Sent message to Player {self.client_player_map.get(writer, 'Unknown')}: {message}")

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
            return True, message
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ValueError):
            print("Data reception error or invalid format.")
            return False, None
        except ConnectionAbortedError:
            print("Connection aborted by Relay Node's TCP Client")
            return False, None

    async def clean_up_connection(self, writer):
        self.client_player_map.pop(writer, None)
        self.connected_clients.discard(writer)  # Remove client from connected clients
        tasks = self.client_tasks.pop(writer, ())
        for task in tasks:
            task.cancel()
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()
        print("Cleaned up connection and closed writer.")
