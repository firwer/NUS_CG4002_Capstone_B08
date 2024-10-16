import asyncio
import threading
from concurrent.futures import Future
from comms.TCPC_Controller import TCPC_Controller


class TCPC_Controller_Sync:
    def __init__(self, ip, port, secret_key):
        self.controller = TCPC_Controller(ip, port, secret_key)
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.start_loop, daemon=True)
        self.loop_thread.start()
        self._connected_event = threading.Event()
        # Start the connection
        future = asyncio.run_coroutine_threadsafe(self._connect(), self.loop)
        future.result()  # Wait for connection to complete

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect(self):
        await self.controller.connect()
        self._connected_event.set()

    def connect(self):
        self._connected_event.wait()  # Wait until connected

    def identify_relay_node(self, player_number):
        future = asyncio.run_coroutine_threadsafe(
            self.controller.identify_relay_node(player_number), self.loop)
        return future.result()  # Wait for the coroutine to finish

    def send(self, message):
        future = asyncio.run_coroutine_threadsafe(self.controller.send_no_encrypt(message), self.loop)
        return future.result()

    def recv_decrypt(self):
        future = asyncio.run_coroutine_threadsafe(self.controller.recv_decrypt(), self.loop)
        return future.result()
