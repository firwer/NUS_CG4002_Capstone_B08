# TCPS_Controller.py
import asyncio
import traceback
from logger_config import setup_logger
from Utils import encrypt_msg, decrypt_message

logger = setup_logger(__name__)

class TCPS_Controller:
    """
    This class handles TCP Server communication between Relay Node <-> U96 (Server).
    It automatically listens for incoming connections and manages message exchanges.
    All received messages from clients are pushed to the respective receive queues.
    All messages to be sent to clients are pushed to the send queue.
    """

    def __init__(self, ip, port, secret_key, receive_queue_p1, receive_queue_p2, send_queue):
        self.secret_key = secret_key
        self.ip = ip
        self.port = port
        self.receive_queue_p1 = receive_queue_p1
        self.receive_queue_p2 = receive_queue_p2
        self.send_queue = send_queue
        self.client_player_map = {}  # Track each client's player number
        self.client_tasks = {}        # Track each client's tasks
        self.connected_clients = set()  # Track connected clients

    async def start_server(self):
        try:
            server = await asyncio.start_server(self.handle_client, host=self.ip, port=self.port)
            logger.info(f"Ultra96 Server started on {self.ip}:{self.port}")

            broadcast_task = asyncio.create_task(self._broadcast_task())  # Start the broadcast task
            async with server:
                await server.serve_forever()
        except Exception as e:
            logger.exception(f"Failed to start TCP server on {self.ip}:{self.port}: {e}")

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logger.info(f"Incoming connection from {addr}. Waiting for identification...")

        # Receive hello packet containing player number from client
        success, message = await self._recv_message(reader)
        if not success:
            logger.error(f"Error in hello packet received from {addr}. Closing connection.")
            writer.close()
            await writer.wait_closed()
            return

        try:
            player_number = int(message.strip())
            self.client_player_map[writer] = player_number
            self.connected_clients.add(writer)
            logger.info(f"Player {player_number} connected from {addr}")
        except ValueError:
            logger.error(f"Invalid player number received from {addr}. Closing connection.")
            writer.close()
            await writer.wait_closed()
            return

        try:
            receive_task = asyncio.create_task(self._receive_task(reader, writer, player_number))
            self.client_tasks[writer] = (receive_task,)
            await receive_task
        except Exception as e:
            logger.exception(f"Exception occurred while handling client {addr}: {e}")
        finally:
            logger.info(f"Closing connection with {addr}")
            await self.clean_up_connection(writer)

    async def _receive_task(self, reader, writer, player_number):
        """Continuously receive messages from the client and place them in the receive_queue."""
        addr = writer.get_extra_info('peername')
        try:
            while True:
                success, message = await self._recv_message(reader)
                if not success:
                    logger.warning(f"Error in data received from Player {player_number}: {addr}. Closing connection.")
                    break
                if player_number == 1:
                    await self.receive_queue_p1.put(message)
                    logger.debug(f"Received message for Player 1: {message}")
                elif player_number == 2:
                    await self.receive_queue_p2.put(message)
                    logger.debug(f"Received message for Player 2: {message}")
                else:
                    logger.warning(f"Invalid player number {player_number} received from {addr}.")
        except Exception as e:
            logger.exception(f"Exception in receiving messages from {addr}: {e}")
        finally:
            await self.clean_up_connection(writer)

    async def _broadcast_task(self):
        logger.info("TCP Server Broadcast task started.")
        """Continuously read messages from send_queue and broadcast them to all connected clients."""
        while True:
            message = await self.send_queue.get()
            logger.info(f"Broadcasting message: {message}")
            await self.broadcast_message(message)

    async def broadcast_message(self, message):
        """Send a message to all connected clients."""
        for writer in list(self.connected_clients):
            try:
                await self._send_message(writer, message)
                logger.debug(f"Sent message to {writer.get_extra_info('peername')}: {message}")
            except Exception as e:
                logger.exception(f"Error sending message to client: {e}")
                await self.clean_up_connection(writer)

    async def _send_message(self, writer, message):
        try:
            writer.write(f"{len(message)}_".encode() + message.encode())
            await writer.drain()
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.exception(f"Failed to send message: {e}")
            raise e

    async def _recv_message(self, reader, timeout=60):
        try:
            data = b''
            while not data.endswith(b'_'):
                chunk = await reader.read(1)
                if not chunk:
                    logger.warning("Client disconnected unexpectedly.")
                    return False, None
                data += chunk
            length = int(data[:-1].decode())
            message = await asyncio.wait_for(reader.readexactly(length), timeout)
            return True, message
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for message.")
            return False, None
        except asyncio.IncompleteReadError:
            logger.error("Incomplete read error. Connection may have been lost.")
            return False, None
        except ValueError:
            logger.error("Invalid message format received.")
            return False, None
        except Exception as e:
            logger.exception(f"Error receiving message: {e}")
            return False, None

    async def clean_up_connection(self, writer):
        addr = writer.get_extra_info('peername')
        try:
            player_number = self.client_player_map.pop(writer, None)
            self.connected_clients.discard(writer)  # Remove client from connected clients
            tasks = self.client_tasks.pop(writer, ())
            for task in tasks:
                task.cancel()
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            logger.info(f"Cleaned up connection and closed writer for {addr}. Player Number: {player_number}")
        except Exception as e:
            logger.exception(f"Error during clean-up for {addr}: {e}")
